# Test File Generation Notes

Commands needed to regenerate generated test fixtures.

## Python Fixtures

```powershell
python generate-test-files.py
```

This covers:

- `test-files/sqlite/good.sqlite`
- `test-files/wave/good.wav`
- `test-files/wave/bad.truncated-data.wav`
- `test-files/images/good.animated.gif`
- `test-files/images/bad.truncated-later-frame.gif`
- `test-files/pdf/bad.stream.badtest.pdf`
- `test-files/m3u8/bad.invalid-utf8.m3u8`
- `test-files/nfo/bad.control-chars.nfo`

## Video Fixture

```powershell
ffmpeg -y -f lavfi -i testsrc=size=16x16:rate=1 -frames:v 1 -pix_fmt yuv420p test-files\videos\good.mp4
```
