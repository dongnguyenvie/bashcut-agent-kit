"""End-to-end checks of what the skills tell agents to do, run against a live BashCut.

Each test drives the running app through its CLI on synthetic media with a known answer (ffmpeg makes it), so a
skill's claim ("media sync gives the offset", "--focus frames the rectangle") is checked against the app itself.

Skips, never fails, when the environment cannot run it:
- no BashCut CLI, or BashCut is not running ($BASHCUT_CLI, the running app's own CLI, then `bashcut` on PATH);
- the CLI lacks the command a test needs (an older BashCut);
- the plugin capability a test needs is not installed or not ready (`plugins list`);
- ffmpeg is missing, or the Vietnamese `say` voice for the speech fixture;
- the project open in BashCut has unsaved changes (the tests open their own project, then reopen the user's).

Run: python3 -m unittest tests.test_e2e_bashcut -v
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

FPS = 30000 / 1001


def find_cli():
    candidates = [os.environ.get("BASHCUT_CLI")]
    ps = subprocess.run(["ps", "-axo", "comm="], capture_output=True, text=True).stdout if shutil.which("ps") else ""
    for line in ps.splitlines():
        if line.endswith("/BashCut.app/Contents/MacOS/BashCutApp"):
            candidates.append(line[: -len("BashCutApp")] + "bashcut")
    candidates.append(shutil.which("bashcut"))
    for c in candidates:
        if c and os.access(c, os.X_OK):
            return c
    return None


class Live:
    """The running BashCut, through its CLI."""

    def __init__(self, cli):
        self.cli = cli
        self.help = subprocess.run([cli, "--help"], capture_output=True, text=True).stdout

    def raw(self, *args, check=True):
        p = subprocess.run([self.cli, *map(str, args)], capture_output=True, text=True, timeout=600)
        if check and p.returncode != 0:
            raise AssertionError(f"bashcut {' '.join(map(str, args))} failed: {p.stderr or p.stdout}")
        return p

    def json(self, *args):
        out = self.raw(*args).stdout
        return json.loads(out) if out.strip() else {}

    def has(self, command):
        return f"bashcut {command} " in self.help or f"bashcut {command}\n" in self.help

    def capabilities(self):
        ready = set()
        for plugin in self.json("plugins", "list").get("plugins", []):
            if plugin.get("availability") == "ready":
                ready.update(p["capability"] for p in plugin.get("providers", []))
        return ready

    def rev(self):
        return self.json("timeline", "get")["rev"]

    def job(self, *args, timeout=600):
        job = self.json(*args)["job"]
        end = time.time() + timeout
        while time.time() < end:
            status = self.json("jobs", "status", job)
            if status.get("state") != "running":
                if status.get("state") != "completed":
                    raise AssertionError(f"job {args} ended {status.get('state')}: {status.get('error')}")
                return status["result"]
            time.sleep(0.5)
        raise AssertionError(f"job {args} timed out")

    def apply(self, ops, label="e2e"):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(ops, f)
        try:
            return self.json("timeline", "apply", f.name, "--base-rev", self.rev(), "--label", label)
        finally:
            os.unlink(f.name)

    def import_media(self, path):
        before = {m["id"] for m in self.json("media", "list")}
        self.raw("media", "import", path, "--base-rev", self.rev())
        new = [m for m in self.json("media", "list") if m["id"] not in before]
        assert len(new) == 1, new
        return new[0]["id"]

    def pixel(self, frame, x, y):
        """RGB of the edit at a timeline frame; x, y as fractions of the picture."""
        png = self.json("ui", "frame", frame)
        w, h = png["width"], png["height"]
        out = subprocess.run(["ffmpeg", "-v", "error", "-i", png["path"], "-vf",
                              f"crop=1:1:{min(int(x * w), w - 1)}:{min(int(y * h), h - 1)}",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        return tuple(out[:3])


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def is_red(c):
    return c[0] > 150 and c[1] < 90 and c[2] < 90


def is_blue(c):
    return c[2] > 150 and c[0] < 90 and c[1] < 90


def is_green(c):
    return c[1] > 150 and c[0] < 90 and c[2] < 90


CLI = find_cli()


@unittest.skipUnless(CLI, "BashCut CLI not found (set BASHCUT_CLI or open BashCut)")
@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg is needed for the fixtures")
class LiveBashCut(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Live(CLI)
        if cls.app.raw("app", "version", check=False).returncode != 0:
            raise unittest.SkipTest("BashCut is not running")
        ctx = cls.app.json("context", "get")
        if ctx.get("dirty"):
            raise unittest.SkipTest("the open BashCut project has unsaved changes")
        cls.previous = ctx.get("project")
        cls.caps = cls.app.capabilities()
        cls.tmp = Path(tempfile.mkdtemp(prefix="bashcut-e2e-"))
        cls.make_fixtures()
        cls.app.raw("project", "create", "--name", "e2e", "--dir", cls.tmp, "--canvas", "portrait", "--fps", "29.97",
                    "--language", "vi")

    @classmethod
    def tearDownClass(cls):
        app = cls.app
        app.raw("project", "close", "--discard-current", check=False)
        if cls.previous:
            app.raw("project", "open", cls.previous, check=False)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        # Every test starts from an empty timeline, even after an earlier test failed half-way.
        items = [i["id"] for t in self.app.json("timeline", "get")["tracks"] for i in t.get("items", [])]
        if items:
            self.app.apply([{"op": "delete", "item": i} for i in items], label="e2e: clear")

    def need(self, command, capability=None):
        if not self.app.has(command):
            self.skipTest(f"this BashCut has no `{command}`")
        if capability and capability not in self.caps:
            self.skipTest(f"no ready plugin provides {capability} (install it: plugins search --capability {capability})")

    # ---------- fixtures ----------

    @classmethod
    def make_fixtures(cls):
        t = cls.tmp
        # Sound with an irregular loudness shape, so its envelope matches at one lag only.
        ffmpeg("-f", "lavfi", "-i", "aevalsrc=(random(0)-0.5)*(0.05+abs(sin(1.3*t)*sin(0.37*t+1)*sin(2.9*t+2))):s=48000:d=60",
               t / "base.wav")
        small = ["-f", "lavfi", "-i", "testsrc=s=320x240:r=30000/1001"]
        # "camera": base 0-40 s. "screen": the same sound 2.5 s later, other mic colour, plus room noise.
        ffmpeg(*small, "-i", t / "base.wav", "-t", 40, "-map", "0:v", "-map", "1:a", "-c:v", "mpeg4", "-c:a", "pcm_s16le",
               t / "camera.mov")
        ffmpeg(*small, "-i", t / "base.wav", "-f", "lavfi", "-i", "anoisesrc=c=pink:a=0.02:d=60:r=48000", "-filter_complex",
               "[1:a]adelay=2500|2500,lowpass=f=3000[d];[d][2:a]amix=inputs=2:normalize=0[a]", "-t", 45,
               "-map", "0:v", "-map", "[a]", "-c:v", "mpeg4", "-c:a", "pcm_s16le", t / "screen.mov")
        # "render played on screen": 12 s of the screen recording from 20 s.
        ffmpeg("-ss", 20, "-i", t / "screen.mov", "-t", 12, "-c:v", "mpeg4", "-c:a", "pcm_s16le", t / "render.mov")
        # Music: one dark (200 + 350 Hz), one bright (2 + 3 kHz).
        ffmpeg("-f", "lavfi", "-i", "aevalsrc=0.3*sin(2*PI*200*t)+0.3*sin(2*PI*350*t):s=48000:d=20", t / "dark.wav")
        ffmpeg("-f", "lavfi", "-i", "aevalsrc=0.3*sin(2*PI*2000*t)+0.3*sin(2*PI*3000*t):s=48000:d=20", t / "bright.wav")
        # A 1920x1080 "desktop": red panel top right, blue panel bottom left, on dark grey.
        ffmpeg("-f", "lavfi", "-i", "color=c=0x202020:s=1920x1080:r=30000/1001:d=6", "-vf",
               "drawbox=x=1500:y=150:w=360:h=480:c=red:t=fill,drawbox=x=120:y=500:w=360:h=480:c=blue:t=fill",
               "-c:v", "mpeg4", "-q:v", 2, t / "desktop.mov")
        # A portrait "camera" in flat green, for the crop box.
        ffmpeg("-f", "lavfi", "-i", "color=c=0x00c000:s=1080x1920:r=30000/1001:d=6", "-c:v", "mpeg4", "-q:v", 2,
               t / "face.mov")

    # ---------- bc:footage-survey: media sync ----------

    def test_media_sync_camera_and_screen(self):
        self.need("media sync", "audio.sync")
        cam, scr = self.app.import_media(self.tmp / "camera.mov"), self.app.import_media(self.tmp / "screen.mov")
        r = self.app.job("media", "sync", "--media", cam, "--to", scr)
        self.assertAlmostEqual(r["offsetSeconds"], 2.5, delta=0.02)
        self.assertTrue(r["reliable"])
        self.assertTrue(r["steady"])
        for half in r["halves"]:
            self.assertAlmostEqual(half["offsetSeconds"], 2.5, delta=0.02)
        # --item maps a placed camera clip's in-point onto the screen recording.
        self.app.apply([{"op": "insert", "track": "v1", "item": {"id": "sync-cam", "media": cam, "at": 0, "dur": 90,
                                                                   "in": round(10 * FPS)}}])
        r = self.app.job("media", "sync", "--media", cam, "--to", scr, "--item", "sync-cam")
        self.assertAlmostEqual(r["item"]["otherSourceSeconds"], 12.5, delta=0.05)
        self.app.apply([{"op": "delete", "item": "sync-cam"}])

    def test_media_sync_finds_a_render_inside_the_screen_recording(self):
        self.need("media sync", "audio.sync")
        scr, ren = self.app.import_media(self.tmp / "screen.mov"), self.app.import_media(self.tmp / "render.mov")
        r = self.app.job("media", "sync", "--media", scr, "--to", ren)
        self.assertAlmostEqual(r["offsetSeconds"], -20.0, delta=0.02)   # render starts at screen 20 s
        self.assertTrue(r["reliable"])

    def test_media_sync_unrelated_sound_is_not_reliable(self):
        self.need("media sync", "audio.sync")
        cam, music = self.app.import_media(self.tmp / "camera.mov"), self.app.import_media(self.tmp / "dark.wav")
        r = self.app.job("media", "sync", "--media", cam, "--to", music)
        self.assertFalse(r["reliable"])

    # ---------- bc:audio-mix: audio measure ----------

    def test_audio_measure_presence_share(self):
        self.need("audio measure", "audio.loudness")
        dark = self.app.job("audio", "measure", "--media", self.app.import_media(self.tmp / "dark.wav"))
        bright = self.app.job("audio", "measure", "--media", self.app.import_media(self.tmp / "bright.wav"))
        for r in (dark, bright):
            for key in ("integratedLUFS", "truePeakDbTP", "loudnessRangeLU", "speechShare", "presenceShare"):
                self.assertIn(key, r)
        # Band edges are 24 dB/octave filters (-6 dB at the edge): tones at 2 and 3 kHz count ~79% and ~58%, so
        # the shares compare tracks rather than give exact fractions (measured: 0.684 for this bright track).
        self.assertLess(dark["presenceShare"], 0.05)
        self.assertGreater(bright["presenceShare"], 0.6)
        self.assertLess(dark["presenceShare"], bright["presenceShare"])

    # ---------- bc:effects: clip motion --focus, crop ----------

    def test_focus_frames_a_panel_and_moves_to_another(self):
        self.need("clip motion")
        if "--focus" not in self.app.help:
            self.skipTest("this BashCut's clip motion has no --focus")
        desk = self.app.import_media(self.tmp / "desktop.mov")
        self.app.apply([{"op": "insert", "track": "v1", "item": {"id": "desk", "media": desk, "at": 0, "dur": 120,
                                                                   "in": 0}}])
        self.app.raw("clip", "motion", "desk", "--focus", "1500,150,360,480", "--focus-to", "120,500,360,480",
                     "--ease", "linear", "--base-rev", self.app.rev())
        first, last = self.app.pixel(0, 0.5, 0.5), self.app.pixel(119, 0.5, 0.5)
        self.assertTrue(is_red(first), first)
        self.assertTrue(is_blue(last), last)
        # The rectangle is framed, not just centred: points well off-centre are still inside the red panel.
        for x, y in ((0.2, 0.5), (0.8, 0.5), (0.5, 0.2), (0.5, 0.8)):
            self.assertTrue(is_red(self.app.pixel(0, x, y)), (x, y))
        self.app.apply([{"op": "delete", "item": "desk"}])

    def test_crop_with_rounded_corners(self):
        self.need("timeline apply")
        # The crop group shipped with media sync; the word "crop" alone also appears in older schemas' text.
        if not self.app.has("media sync"):
            self.skipTest("this BashCut has no crop group")
        face = self.app.import_media(self.tmp / "face.mov")
        self.app.apply([{"op": "insert", "track": "v2", "item": {"id": "face", "media": face, "at": 0, "dur": 60, "in": 0}},
                        {"op": "setProperties", "item": "face",
                         "patch": {"crop": {"left": 0.25, "right": 0.25, "top": 0.25, "bottom": 0.25, "radius": 0.3}}}])
        self.assertTrue(is_green(self.app.pixel(30, 0.5, 0.5)))           # inside the box
        self.assertFalse(is_green(self.app.pixel(30, 0.1, 0.5)))          # cropped side
        self.assertFalse(is_green(self.app.pixel(30, 0.5, 0.1)))          # cropped top
        self.assertFalse(is_green(self.app.pixel(30, 0.255, 0.255)))      # rounded corner cut off
        self.assertTrue(is_green(self.app.pixel(30, 0.3, 0.5)))           # straight edge kept
        # An uneven crop keeps the visible part where it was in the picture (here x 0.3-1.0); pan by
        # (left - right) / 2 x canvas width x zoom brings it back to the centre (x 0.15-0.85).
        uneven = {"left": 0.3, "right": 0, "top": 0.25, "bottom": 0.25, "radius": 0}
        self.app.apply([{"op": "setProperties", "item": "face", "patch": {"crop": uneven}}])
        self.assertFalse(is_green(self.app.pixel(30, 0.2, 0.5)))
        self.assertTrue(is_green(self.app.pixel(30, 0.95, 0.5)))
        self.app.apply([{"op": "setProperties", "item": "face",
                         "patch": {"crop": uneven, "transform": {"zoom": 1, "pan": -(0.3 - 0) / 2 * 1080, "tilt": 0}}}])
        self.assertTrue(is_green(self.app.pixel(30, 0.2, 0.5)))
        self.assertFalse(is_green(self.app.pixel(30, 0.9, 0.5)))
        self.app.apply([{"op": "delete", "item": "face"}])

    # ---------- bc:captions-text: ranged transcription, loop review ----------

    def test_captions_generate_one_stretch(self):
        self.need("captions generate", "captions.transcribe")
        if "--from" not in self.app.help:
            self.skipTest("this BashCut's captions generate has no --from/--to")
        voices = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout if shutil.which("say") else ""
        if "Linh" not in voices:
            self.skipTest("needs macOS `say` with the Vietnamese voice Linh for the speech fixture")
        lines = ["Xin chào các bạn.", "Hôm nay mình giới thiệu một công cụ dựng video.", "Cảm ơn mọi người đã xem."]
        for i, text in enumerate(lines):
            subprocess.run(["say", "-v", "Linh", "-o", str(self.tmp / f"l{i}.aiff"), text], check=True)
        ffmpeg("-f", "lavfi", "-i", "testsrc=s=320x240:r=30000/1001", *sum((["-i", self.tmp / f"l{i}.aiff"]
               for i in range(3)), []), "-filter_complex",
               "[1:a]adelay=2000|2000[a];[2:a]adelay=12000|12000[b];[3:a]adelay=24000|24000[c];"
               "[a][b][c]amix=inputs=3:normalize=0,aresample=48000,apad[o]", "-t", 30, "-map", "0:v", "-map", "[o]",
               "-c:v", "mpeg4", "-c:a", "pcm_s16le", self.tmp / "talk.mov")
        talk = self.app.import_media(self.tmp / "talk.mov")
        self.app.apply([{"op": "insert", "track": "v1", "item": {"id": "talk", "media": talk, "at": 0,
                                                                   "dur": round(28 * FPS), "in": 0}}])
        # The skill's order: transcribe the whole clip, then redo one stretch with --from/--to --replace.
        self.app.job("captions", "generate", "--media", talk)
        before = self.captions()
        self.assertTrue(any(s < 5 for s, _, _ in before), before)          # line at 2 s
        self.assertTrue(any(s > 22 for s, _, _ in before), before)         # line at 24 s
        self.app.job("captions", "generate", "--media", talk, "--from", 10, "--to", 20, "--replace")
        after = self.captions()
        inside = [c for c in after if 10 <= c[0] < 20]
        self.assertTrue(inside, after)
        # Only the stretch was swapped: captions outside it are untouched and nothing is duplicated.
        self.assertEqual([c for c in before if not 10 <= c[0] < 20], [c for c in after if not 10 <= c[0] < 20])
        self.assertEqual(len({c[0] for c in inside}), len(inside), after)
        # A ranged run alone transcribes only its stretch.
        captions = [i["id"] for t in self.app.json("timeline", "get")["tracks"] if t.get("role") == "captions"
                    for i in t.get("items", [])]
        self.app.apply([{"op": "delete", "item": i} for i in captions], label="e2e: clear captions")
        self.app.job("captions", "generate", "--media", talk, "--from", 10, "--to", 20)
        for start, end, _ in self.captions():
            self.assertGreaterEqual(start, 9.5)
            self.assertLessEqual(end, 20.5)

    def captions(self):
        out = self.app.raw("captions", "export").stdout.strip()
        return parse_srt(json.loads(out) if out.startswith('"') else out)   # the CLI prints the SRT as a JSON string

    def test_review_flags_a_recognition_loop(self):
        self.need("review run")
        if not self.app.has("media sync"):     # the loop check shipped with media sync and ranged captions
            self.skipTest("this BashCut's review does not check captions for recognition loops")
        srt = self.tmp / "loop.srt"
        srt.write_text("1\n00:00:01,000 --> 00:00:14,000\nà à à à à à à à à à à à\n\n"
                       "2\n00:00:15,000 --> 00:00:17,000\nCâu bình thường.\n", encoding="utf-8")
        self.app.raw("captions", "import", srt, "--base-rev", self.app.rev(), "--replace")
        review = self.app.raw("review", "run").stdout
        self.assertIn("recognition loop", review.lower())


def parse_srt(text):
    def sec(t):
        h, m, s = t.replace(",", ".").split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    cues = []
    for block in text.strip().split("\n\n"):
        rows = block.strip().splitlines()
        if len(rows) >= 3 and "-->" in rows[1]:
            a, b = (x.strip() for x in rows[1].split("-->"))
            cues.append((sec(a), sec(b), " ".join(rows[2:])))
    return cues


if __name__ == "__main__":
    unittest.main()
