import math
from pathlib import Path

import git
from icecream import ic
from tqdm import tqdm

############################
###        INPUTS        ###
############################

# Path to local git repo
input_path = Path.home() / "Documents" / "DESY" / "dissertation_copy"

# Git branch
branch = "master"

# Name of the (input) paper file (without extension)
filename = "main"

# Path to output folder
output_path = Path.home() / "Desktop" / "papermovie_output" / "output"
output_path.mkdir(parents=True, exist_ok=True)

# Video size (by default Full HD)
total_width = 3840
total_height = 2160

# Video frames per second
# Use low values (< 5) on papers with many pages (> 50).
# It will give a better results, since there is much more to look at. ;-)
fps = 2

############################
### RETRIEVING PDF FILES ###
############################

repo = git.Repo(input_path)

num_commits = len(list(repo.iter_commits(branch)))
last_commit = list(repo.iter_commits(branch))[-1]
ic(last_commit)

max_page_num = 0

print("Start retrieving PDFs")
ic(list(enumerate(repo.iter_commits(branch)))[:3])
for i, commit in tqdm(list(enumerate(repo.iter_commits(branch)))[:3]):
    print(f"Retrieving PDF revision {i+1}/{num_commits} ...")

    # Check out old commits
    ic(commit)
    repo.git.checkout(commit)

    # Compile tex with references
    repo.git.execute(
        ["pdflatex", "-synctex=1", "-interaction=nonstopmode", f"{filename}.tex"]
    )
    repo.git.execute(["bibtex", f"{filename}.aux"])
    repo.git.execute(
        ["pdflatex", "-synctex=1", "-interaction=nonstopmode", f"{filename}.tex"]
    )
    repo.git.execute(["bibtex", f"{filename}.aux"])
    repo.git.execute(
        ["pdflatex", "-synctex=1", "-interaction=nonstopmode", f"{filename}.tex"]
    )

    # Find maximum number of pages
    pages = repo.git.execute(["pdfinfo", f"{filename}.pdf"]).split("\n")
    pages = [int(page.split()[1]) for page in pages if page.startswith("Pages")][0]
    if pages > max_page_num:
        max_page_num = pages

    # Move pdf to output folder
    format_filename = f"{i+1:03d}"
    repo.git.execute(["cp", f"{filename}.pdf", f"{output_path / format_filename}.pdf"])

# Revert back to last commit
repo.git.checkout(last_commit)

############################
###    CREATING IMAGES   ###
############################

# The width/height ratio of A4 paper
ratio_a4 = 0.7070

# The height of an individual tile
tile_height = (total_width * total_height / (ratio_a4 * max_page_num)) ** 0.5
tile_width = tile_height * ratio_a4
ic(tile_height, tile_width)

# Calculate grid
num_tiles_height = total_height / tile_height
num_tiles_width = total_width / tile_width
ic(num_tiles_height, num_tiles_width)

# Ceil tiles to integers
num_tiles_height = math.ceil(num_tiles_height)
num_tiles_width = math.ceil(num_tiles_width)
ic(num_tiles_height, num_tiles_width)

# Report measurements
print("Movie measurements:")
print(f"Number of horizontal tiles: {num_tiles_width}")
print(f"Number of vertical tiles: {num_tiles_height}")

# Have ceiled the number of tiles, they exceed the total_width and total_height.
# So, we also need to recalculate the tile_height and tile_width. This step will
# (slightly) change the A4 ratio, but it beats half pages in the video.
tile_height = total_height / num_tiles_height
tile_width = total_width / num_tiles_width
ic(tile_height, tile_width)

# Generate images
print("Start generating images ...")
for i in tqdm(range(3)):  # num_commits)):
    format_filename = f"{i+1:03d}"
    repo.git.execute(
        [
            "montage",
            f"{output_path / format_filename}.pdf",
            "-tile",
            f"{num_tiles_width}x{num_tiles_height}",
            "-background",
            "white",
            "-geometry",
            f"{tile_width}x{tile_height}",
            "-alpha",
            "remove",
            "-colorspace",
            "sRGB",
            f"{output_path / format_filename}.png",
        ]
    )
    print(f"Image #{format_filename} generated!")

############################
###     RENDER MOVIE     ###
############################

print("Start rendering movie ...")
repo.git.execute(
    [
        "ffmpeg",
        "-r",
        f"{fps}",
        "-i",
        f"{output_path / '%03d.png'}",
        "-pix_fmt",
        "yuv420p",
        "-b",
        "8000k",
        "-vcodec",
        "libx264",
        f"{output_path / filename}.mp4",
    ]
)

############################
###     CLEANUP STUFF    ###
############################

print("Movie rendered, cleaning up ... or not")

print(f"Movie available at {output_path / filename}.mp4")
