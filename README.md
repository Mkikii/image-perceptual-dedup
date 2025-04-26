# Image Perceptual Deduplication

A Python tool that removes duplicate images from ZIP archives using perceptual hashing. This tool can detect and remove similar images even if they've been resized, compressed, or slightly modified.

## Features
- Identifies similar images using average hash algorithm
- Processes ZIP archives while preserving directory structure
- Supports multiple image formats (PNG, JPG, JPEG, BMP, GIF, TIFF)
- Uses perceptual hashing with configurable similarity threshold
- Maintains original file hierarchy in output
- Provides detailed processing feedback
- Handles errors gracefully with automatic cleanup

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/image-perceptual-dedup.git
cd image-perceptual-dedup
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python perceptual_dedup.py input.zip output_directory
```

Extended usage with size limits:
```bash
python perceptual_dedup.py input.zip output_directory --max-zip-size 2147483648 --max-image-size 52428800
```

### Parameters
- `input_zip`: Path to the input ZIP file
- `output_dir`: Directory where the output ZIP file will be created
- `--max-zip-size`: Maximum ZIP file size in bytes (default: 1GB)
- `--max-image-size`: Maximum individual image size in bytes (default: 50MB)

The script will:
1. Extract images from the input ZIP
2. Process each image to identify duplicates
3. Create a new ZIP file containing only unique images
4. Clean up temporary files automatically

## Technical Details

- Hash size: 8x8 (64-bit fingerprint)
- Hamming distance threshold: 5 (adjustable in code)
- Supported image formats: PNG, JPG, JPEG, BMP, GIF, TIFF
- Uses PIL/Pillow for image processing
- Temporary files are automatically cleaned up
- Memory efficient - processes images one at a time
- Performance optimizations:
  - Groups similar images by hash to reduce comparisons
  - Uses tuple-based hash dictionary for efficient lookups
  - Encapsulated duplicate detection logic for better maintainability
  - Optimized for handling large datasets with minimal memory footprint

## Configuration

You can modify these constants in the script:
```python
HASH_SIZE = 8  # Size of the hash (8x8 = 64 bits)
HASH_DIFF_THRESHOLD = 5  # Similarity threshold
VALID_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
```

## Future Improvements

Planned features:
- Add command line options for hash size and similarity threshold
- Support for processing directories without requiring ZIP
- Parallel processing for faster execution
- Option to save list of duplicates
- GUI interface
- Progress bar for large archives
- Support for more image formats
- Option to preview duplicates before removal

## Requirements

- Python 3.x
- Pillow >= 10.0.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security Note

The script processes images locally and doesn't transmit any data. All temporary files are automatically cleaned up after processing.
