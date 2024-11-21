# Paper-Lapse

I recently finished writing my doctoral dissertation and thought, wouldn't it be fun to make a time-lapse of the dissertation being written? Luckily, I wasn't the first to have this idea. I found the [_paper2movie_](https://github.com/momentofgeekiness/paper2movie) script by Raymond Vermaas, which does exactly that. However, the script was 11 years old and didn't quite work out of the box anymore. The original script also generated one frame per commit, meaning that time would pass at different speeds depending on when commits were made. I wanted time to pass at a constant rate.

_Paper-Lapse_ is a rewrite of the original [_paper2movie_](https://github.com/momentofgeekiness/paper2movie) script in Python. I believe the latter was itself based on the [_paper-movies_](https://github.com/brownsys/paper-movies) scripts by Andrew Ferguson.

Like the original script, this script generates a time-lapse video of a git-versioned LaTeX document. To do this, it loops over all commits and generates a PDF for each of them. The PDFs are then converted to images with the `montage` tool from _ImageMagick_, arranging the pages of the PDFs in a grid. Then the script creates a directory full of frames enumerated in the order they should appear in the final video. Finally, the images are combined into a video using `ffmpeg`.

Unlike the original script, _Paper-Lapse_ is written in Python. The script is generally refactored, and now allows the user to choose whether frames in the final video are arranged one for each commit or one for each day (specifically representing the state at the end of the day). An additional mode arranging frames by the smallest time interval between commits is also implemented though currently not usable because it likely generated too many frames to handle.

## Requirements

- A Unix-like operating system (tested on macOS Sequoia)
- A LaTeX document in a directory with git version control
- Instalations of:
  - A LaTeX distribution
  - Git
  - Python
  - ImageMagick
  - FFMPEG with the libx264 encoder

The best way to install these dependencies is probably your favourite package manager, e.g. Homebrew on macOS.

You will also need to install some Python packages, for example using `pip`:

```bash
pip install GitPython pytz icecream tqdm
```

## Usage

1. Open the script file with your favourite text editor and edit the input parameters at the top of the file.
2. Run the script with

```bash
python paper-lapse.py
```

3. Enjoy your paper time-lapse!

## Examples

Here are some examples generated with the original and other scripts that look like the output of the _Paper-Lapse_ script:

- Original inspiration by Tim Weninger: https://youtu.be/hNENiG7LAnc
- Master's thesis by Raymond Vermaas (author of the original _paper2movie_ script): https://youtu.be/wprkTENOJHE
- Papers by Andrew Ferguson (author of the _paper-movies_ scripts):
  - https://youtu.be/QBEEoIM2PBQ
  - https://youtu.be/nyLSJjntK6I
  - https://youtu.be/MIrCSRjqpnA
  - https://youtu.be/6oVqt5sW6qg
  - https://youtu.be/sibJhiDRdSw
