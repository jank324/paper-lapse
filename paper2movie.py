import math
import subprocess
from pathlib import Path

import git
from tqdm import tqdm

# ------- INPUTS ------------------------------------

# Path to local git repo
input_path = Path.home() / "Documents" / "DESY" / "dissertation_copy"

# Git branch
branch = "master"

# Name of the (input) paper file (without extension)
filename = "main"

# Path to output folder
output_path = Path.home() / "Desktop" / "papermovie_output" / "output"

# Video size (by default Full HD)
total_width = 3840
total_height = 2160

# Video frames per second
# Use low values (< 5) on papers with many pages (> 50).
# It will give a better results, since there is much more to look at. ;-)
fps = 2


def generate_pdfs(repo: git.Repo) -> None:
    """
    Generate PDFs by looping through all past commits on the brange and rendering the
    LaTeX project.
    """
    output_path.mkdir(parents=True, exist_ok=True)
    last_commit = list(repo.iter_commits(branch))[-1]

    for i, commit in tqdm(
        list(enumerate(repo.iter_commits(branch)))[:3], desc="Generating PDFs ..."
    ):
        # Check out old commit
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

        # Move generated pdf to output folder
        (input_path / f"{filename}.pdf").rename(output_path / f"{i+1:03d}.pdf")

    # Revert back to last commit
    repo.git.checkout(last_commit)


def find_maximum_number_of_pages(output_path):
    """Find maximum number of pages in the generated PDFs."""
    print("Finding maximum number of pages ...", end=" ")
    max_page_num = 0
    for pdf in output_path.glob("*.pdf"):
        pages = subprocess.run(
            ["pdfinfo", pdf], stdout=subprocess.PIPE, text=True
        ).stdout.split("\n")
        pages = [int(page.split()[1]) for page in pages if page.startswith("Pages")][0]
        if pages > max_page_num:
            max_page_num = pages

    print(f"{max_page_num}")

    return max_page_num


def compute_tile_sizes(total_width, total_height, max_page_num):
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
    output_path, num_tiles_width, num_tiles_height, tile_width, tile_height
):
    """Generate images from PDFs."""
    for i in tqdm(range(3), desc="Generating images ..."):
        # num_commits)):
        filename = f"{i+1:03d}"
        subprocess.run(
            [
                "montage",
                f"{output_path / filename}.pdf",
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
                f"{output_path / filename}.png",
            ]
        )


def render_movie():
    """Render movie from images."""
    print("Rendering movie ...")
    subprocess.run(
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


def main():
    repo = git.Repo(input_path)

    generate_pdfs(repo)
    max_page_num = find_maximum_number_of_pages(output_path)
    grid_width, grid_height, tile_width, tile_height = compute_tile_sizes(
        total_width, total_height, max_page_num
    )
    generate_images(output_path, grid_width, grid_height, tile_width, tile_height)
    render_movie()

    print("Movie rendered, cleaning up ... or not")

    print(f"Movie available at {output_path / filename}.mp4")


if __name__ == "__main__":
    main()
