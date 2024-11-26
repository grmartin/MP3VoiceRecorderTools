import sys
from pyinstaller_versionfile import create_versionfile

def main():
    if len(sys.argv) != 2:
        print("Usage: python gen_version.py <output_file>")
        sys.exit(1)

    output_file = sys.argv[1]

    create_versionfile(
        output_file=output_file,
        version="1.0.0.0",
        company_name="Glenn R. Martin",
        file_description="This is a CLI/Droplet application to tag dates on MP3s provided or recursively in directories provided within their TXXX ID3 Tags.",
        internal_name="TagDatesOnMP3",
        legal_copyright="Copyright © 2024 Glenn R. Martin",
        original_filename="TagDatesOnMP3.exe",
        product_name="TagDatesOnMP3"
    )
    print(f"Version file generated: {output_file}")

if __name__ == "__main__":
    main()