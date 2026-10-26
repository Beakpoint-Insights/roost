# The README demo: a made-up roost orchestrator session (the example team, Acme).
# Re-record it with VHS (https://github.com/charmbracelet/vhs) from the repo root:
#
#   vhs demo/roost.tape && gifsicle -b -O3 --colors 64 --lossy=30 demo/roost.gif
#
# gifsicle (https://www.lcdf.org/gifsicle/) shrinks the GIF to about half, so the README loads quickly.
#
# demo/replay.py prints roost's side; this file types the user's side and sets the timing.

Output demo/roost.gif

Set Shell "bash"
Set FontSize 16
Set Width 1300
Set Height 860
Set Padding 24
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms
Set WindowBar Colorful
Set WindowBarSize 36
Set Framerate 15

Hide
Type "clear && python3 demo/replay.py" Enter
Sleep 1s
Show

Sleep 1s
Type "/roost:shape-epic Let customers invite teammates to their workspace"
Sleep 600ms
Enter
Sleep 11s

Type "1A 2A 3A"
Sleep 500ms
Enter
Sleep 7.5s

Type "build PROJ-1234"
Sleep 500ms
Enter
Sleep 11.5s

Type "approve"
Sleep 500ms
Enter
Sleep 10s

Type "done"
Sleep 500ms
Enter
Sleep 6s

Type "What's the status on PROJ-1234?"
Sleep 500ms
Enter
Sleep 15s

Type "as recommended"
Sleep 500ms
Enter
Sleep 9s

Type "ok"
Sleep 500ms
Enter
Sleep 7s

Type "What's the status on PROJ-1234?"
Sleep 500ms
Enter
Sleep 15s

Type "ok"
Sleep 500ms
Enter
Sleep 9s

Type "let's run the PROJ-1240 runbook together"
Sleep 500ms
Enter
Sleep 10s

Type "Applied 1 migration: 20261023_add_invitations"
Sleep 500ms
Enter
Sleep 12s
