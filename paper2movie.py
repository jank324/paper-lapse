import math
import shutil
import subprocess
from datetime import timedelta
from pathlib import Path
from typing import Literal

import git
from tqdm import tqdm

# ------- INPUTS ------------------------------------

# Path to local git repo
input_dir = Path.home() / "Documents" / "DESY" / "dissertation_copy"

# Git branch
branch = "master"

# Name of the (input) paper file (without extension)
paper_name = "main"

# Path to output folder
output_dir = Path.home() / "Desktop" / "papermovie_output" / "output"

# Video size (by default Full HD)
total_width = 3840
total_height = 2160

# Video frames per second
# Use low values (< 5) on papers with many pages (> 50).
# It will give a better results, since there is much more to look at. ;-)
fps = 2

# Timing
# "commits" - Generate one frame for each commit
# "days" - Generate one frame for state at the end of each day
# "realtime" - Generate one frame for each of the smallest time interval between commits
timing = "days"


def generate_pdfs(repo: git.Repo, pdf_dir: Path) -> None:
    """
    Generate PDFs by looping through all past commits on the brange and rendering the
    LaTeX project.
    """
    pdf_dir.mkdir(parents=True, exist_ok=True)

    last_commit = list(repo.iter_commits(branch))[-1]

    for i, commit in tqdm(
        list(enumerate(repo.iter_commits(branch)))[:3], desc="Generating PDFs ..."
    ):
        output_filename = pdf_dir / f"{commit.hexsha}.pdf"

        # Check that file doesn't already exist
        if output_filename.exists():
            continue

        # Check out old commit
        repo.git.checkout(commit)

        # Compile tex with references
        repo.git.execute(
            ["pdflatex", "-synctex=1", "-interaction=nonstopmode", f"{paper_name}.tex"]
        )
        repo.git.execute(["bibtex", f"{paper_name}.aux"])
        repo.git.execute(
            ["pdflatex", "-synctex=1", "-interaction=nonstopmode", f"{paper_name}.tex"]
        )
        repo.git.execute(["bibtex", f"{paper_name}.aux"])
        repo.git.execute(
            ["pdflatex", "-synctex=1", "-interaction=nonstopmode", f"{paper_name}.tex"]
        )

        # Move generated pdf to output folder
        (input_dir / f"{paper_name}.pdf").rename(output_filename)

    # Revert back to last commit
    repo.git.checkout(last_commit)


def find_maximum_number_of_pages(pdf_dir: Path) -> int:
    """Find maximum number of pages in the generated PDFs."""
    print("Finding maximum number of pages ...", end=" ")
    max_page_num = 0
    for pdf in pdf_dir.glob("*.pdf"):
        pages = subprocess.run(
            ["pdfinfo", pdf], stdout=subprocess.PIPE, text=True
        ).stdout.split("\n")
        pages = [int(page.split()[1]) for page in pages if page.startswith("Pages")][0]
        if pages > max_page_num:
            max_page_num = pages

    print(f"{max_page_num}")

    return max_page_num


def compute_tile_sizes(total_width: int, total_height: int, max_page_num: int) -> tuple:
    """Compute the title size and numbers of tiles to fit into the image."""
    print("Computing tile sizes ...")

    # The width/height ratio of A4 paper
    ratio_a4 = 0.7070

    # The width and height of an individual tile
    tile_height = (total_width * total_height / (ratio_a4 * max_page_num)) ** 0.5
    tile_width = tile_height * ratio_a4

    # Calculate grid
    grid_height = math.ceil(total_height / tile_height)
    grid_width = math.ceil(total_width / tile_width)

    # Have ceiled the number of tiles, they exceed the total_width and total_height.
    # So, we also need to recalculate the tile_height and tile_width. This step will
    # (slightly) change the A4 ratio, but it beats half pages in the video.
    tile_height = total_height / grid_height
    tile_width = total_width / grid_width

    print(f"    ... Grid size: {grid_width} x {grid_height}")
    print(f"    ... Tile size: {tile_width} x {tile_height}")

    return grid_width, grid_height, tile_width, tile_height


def generate_images(
    pdf_dir: Path,
    image_dir: Path,
    grid_width: int,
    grid_height: int,
    tile_width: float,
    tile_height: float,
) -> None:
    """Generate images from PDFs."""
    image_dir.mkdir(parents=True, exist_ok=True)

    for input_pdf_file in tqdm(
        list(pdf_dir.glob("*.pdf")), desc="Generating images ..."
    ):
        output_png_file = image_dir / f"{input_pdf_file.stem}.png"

        # Check if image already exists
        if output_png_file.exists():
            continue

        # Generate image if it does not exist
        subprocess.run(
            [
                "montage",
                input_pdf_file,
                "-tile",
                f"{grid_width}x{grid_height}",
                "-background",
                "white",
                "-geometry",
                f"{tile_width}x{tile_height}",
                "-alpha",
                "remove",
                "-colorspace",
                "sRGB",
                output_png_file,
            ]
        )


def arrange_images(
    mode: Literal["commits", "days", "realtime"],
    repo: git.Repo,
    image_dir: Path,
    arranged_dir: Path,
) -> None:
    """Create a directory with images named with frame indices."""
    arranged_dir.mkdir(parents=True, exist_ok=True)

    commits = list(repo.iter_commits(branch))[:3]

    if mode == "commits":
        for i, commit in enumerate(
            reversed(tqdm(commits, desc="Arranging images by commits ..."))
        ):
            input_image = image_dir / f"{commit.hexsha}.png"
            output_image = arranged_dir / f"{i:03d}.png"
            shutil.copy(input_image, output_image)

    elif mode == "days":
        commit_days = [commit.committed_datetime.date() for commit in commits]
        first_day = min(commit_days)
        last_day = max(commit_days)

        # Make list of all days between first and last day
        days = [first_day]
        while days[-1] < last_day:
            days.append(days[-1] + timedelta(days=1))

        for i, day in enumerate(days):
            # Find the latest commit before the end of the day
            for commit in commits:
                if commit.committed_datetime.date() <= day:
                    break

            input_image = image_dir / f"{commit.hexsha}.png"
            output_image = arranged_dir / f"{i:03d}.png"
            shutil.copy(input_image, output_image)

    elif mode == "realtime":
        pass


def render_movie(image_dir: Path, output_filename: Path) -> None:
    """Render movie from images."""
    print("Rendering movie ...")
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-r",
            f"{fps}",
            "-i",
            f"{image_dir / '%03d.png'}",
            "-pix_fmt",
            "yuv420p",
            "-b",
            "8000k",
            "-vcodec",
            "libx264",
            f"{output_filename}.mp4",
        ]
    )


def main():
    repo = git.Repo(input_dir)

    generate_pdfs(repo, output_dir / "pdfs")
    max_page_num = find_maximum_number_of_pages(output_dir / "pdfs")
    grid_width, grid_height, tile_width, tile_height = compute_tile_sizes(
        total_width, total_height, max_page_num
    )
    generate_images(
        output_dir / "pdfs",
        output_dir / "images",
        grid_width,
        grid_height,
        tile_width,
        tile_height,
    )
    arrange_images(timing, repo, output_dir / "images", output_dir / "arranged")
    render_movie(output_dir / "arranged", output_dir / paper_name)

    print("Movie rendered, cleaning up ... or not")
    # (output_dir / "arranged").unlink()

    print(f"Movie available at {output_dir / paper_name}.mp4")


if __name__ == "__main__":
    main()
