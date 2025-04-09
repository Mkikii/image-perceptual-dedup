import zipfile
import os
import tempfile
from PIL import Image, ImageFilter
from PIL.Image import Resampling
import shutil
import argparse
import sys
import stat

# Constants
HASH_SIZE = 8  # produces an 8x8 hash (64 bits)
HASH_DIFF_THRESHOLD = 5  # threshold for considering images similar
MAX_ZIP_SIZE = 1024 * 1024 * 1024  # 1GB
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB


def average_hash(image, hash_size=HASH_SIZE):
    """
    Compute the average hash of the image.
    Steps:
    1. Convert image to grayscale.
    2. Resize to hash_size x hash_size.
    3. Compute average pixel value.
    4. Create hash: 1 if pixel >= average, else 0.
    Returns a list of bits.
    """
    # Convert to grayscale and resize
    image = image.convert("L").resize((hash_size, hash_size), Resampling.LANCZOS)
    pixels = list(image.getdata())
    avg = sum(pixels) / len(pixels)
    # Create binary hash
    bits = [1 if pixel >= avg else 0 for pixel in pixels]
    return bits


def hamming_distance(hash1, hash2):
    """
    Compute the Hamming distance between two hashes (lists of bits).
    """
    return sum(el1 != el2 for el1, el2 in zip(hash1, hash2))


# Define list of valid image extensions
VALID_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}

# Create temporary directories for extraction and for storing unique images
temp_extract_dir = tempfile.mkdtemp(prefix="extract_")
temp_unique_dir = tempfile.mkdtemp(prefix="unique_")

os.chmod(temp_extract_dir, stat.S_IRWXU)  # User only permissions
os.chmod(temp_unique_dir, stat.S_IRWXU)

# Set up argument parser
parser = argparse.ArgumentParser(description='Process images from zip file and remove duplicates.')
parser.add_argument('input_zip', help='Path to the input zip file')
parser.add_argument('output_dir', help='Directory to store the output zip file')
parser.add_argument('--max-zip-size', type=int, default=MAX_ZIP_SIZE,
                   help='Maximum zip file size in bytes')
parser.add_argument('--max-image-size', type=int, default=MAX_IMAGE_SIZE,
                   help='Maximum individual image size in bytes')

try:
    args = parser.parse_args()

    # Validate input zip file
    if not os.path.exists(args.input_zip):
        print(f"Error: Input zip file not found: {args.input_zip}")
        sys.exit(1)

    # Check zip file size
    zip_size = os.path.getsize(args.input_zip)
    if zip_size > args.max_zip_size:
        print(f"Error: ZIP file too large ({zip_size} bytes). Maximum allowed: {args.max_zip_size} bytes")
        sys.exit(1)

    # Validate zip file integrity
    try:
        with zipfile.ZipFile(args.input_zip, 'r') as zip_ref:
            if zip_ref.testzip() is not None:
                print("Error: ZIP file is corrupted")
                sys.exit(1)

            # Check for zip bombs
            total_size = sum(info.file_size for info in zip_ref.filelist)
            if total_size > args.max_zip_size * 10:  # Compression ratio > 10
                print("Error: Suspicious ZIP file detected (possible zip bomb)")
                sys.exit(1)

    except zipfile.BadZipFile:
        print("Error: File is not a valid ZIP archive")
        sys.exit(1)

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Update paths
    zip_path = args.input_zip
    unique_zip_path = os.path.join(args.output_dir, 'unique_images.zip')

    # Extract the zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)

    print(f"Extracted files to {temp_extract_dir}")

    # Gather image file paths from extracted directory (recursively)
    image_files = []
    for root, dirs, files in os.walk(temp_extract_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in VALID_EXTENSIONS:
                image_files.append(os.path.join(root, file))

    print(f"Found {len(image_files)} image files.")

    unique_hashes = []
    unique_filepaths = []
    duplicates = []

    for img_path in image_files:
        try:
            # Check image file size
            if os.path.getsize(img_path) > args.max_image_size:
                print(f"Skipping {img_path}: File too large")
                continue

            with Image.open(img_path) as img:
                # Validate image file
                img.verify()
                img.load()  # Required to catch potential truncated images
                img_hash = average_hash(img)

        except (IOError, SyntaxError, ValueError) as e:
            print(f"Error processing {img_path}: Invalid or corrupted image - {e}")
            continue
        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            continue

        # Check against all previously stored unique hashes
        is_dup = False
        for uhash in unique_hashes:
            if hamming_distance(img_hash, uhash) <= HASH_DIFF_THRESHOLD:
                is_dup = True
                break
        if is_dup:
            duplicates.append(img_path)
        else:
            unique_hashes.append(img_hash)
            unique_filepaths.append(img_path)

    print(
        f"Identified {len(unique_filepaths)} unique images and {len(duplicates)} duplicates.")

    # Copy unique images to the unique directory, preserving relative structure
    for file_path in unique_filepaths:
        # Compute relative path from extraction folder
        rel_path = os.path.relpath(file_path, temp_extract_dir)
        dest_path = os.path.join(temp_unique_dir, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(file_path, dest_path)

    # Create a zip archive of the unique images folder
    with zipfile.ZipFile(unique_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_unique_dir):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_file = os.path.relpath(abs_file, temp_unique_dir)
                zipf.write(abs_file, arcname=rel_file)

    print(f"Unique images have been zipped at {unique_zip_path}")

    # Clean up temporary directories
    shutil.rmtree(temp_extract_dir)
    shutil.rmtree(temp_unique_dir)

except Exception as e:
    print(f"An error occurred: {e}")
    # Clean up temporary directories in case of error
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)
    if os.path.exists(temp_unique_dir):
        shutil.rmtree(temp_unique_dir)
    sys.exit(1)
