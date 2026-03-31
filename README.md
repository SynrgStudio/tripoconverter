# Tripo 3D Converter

This tool automates a Tripo Studio workflow:

1. Open a Tripo workspace URL in a headless browser.
2. Detect the `.glb` file requested by the page.
3. Download the original GLB.
4. Run `gltf-transform dequantize` to remove mesh quantization and meshopt compression.
5. Delete the original input so only the cleaned `_ready.glb` remains.

It also supports local `.glb` and `.gltf` files directly.

## Requirements

- Windows
- Python 3.10 or newer recommended
- Node.js with `npm`

The script can install these Python packages automatically when needed:

- `playwright`
- `requests`

The script can also install `@gltf-transform/cli` automatically through `npm`.

If Node.js is not installed, automatic installation of `gltf-transform` will not be possible.

## How it works

The script uses Playwright to launch Chromium and listen to network requests. That is how it finds the actual `.glb` URL behind a Tripo page such as:

```text
https://studio.tripo3d.ai/workspace/generate/your-model-id
```

Tripo often serves files with names like:

```text
tripo_pbr_model_<id>_meshopt.glb
```

The script prefers URLs containing:

- `meshopt`
- `tripo_pbr_model`

## Installation

1. Install Python.
2. Install Node.js from https://nodejs.org/.
3. Open a terminal in this folder.
4. Run the script with a URL or a local file.

On first run, the script will attempt to install any missing Python packages and `@gltf-transform/cli` automatically.

## Usage

### Interactive mode

Run the script with no arguments:

```bash
python convert_tripo.py
```

You will get a prompt where you can paste:

- a Tripo workspace URL
- a local `.glb` file path
- a local `.gltf` file path

Press Enter on an empty line to exit.

### Argument mode

Pass the URL or file path directly:

```bash
python convert_tripo.py "https://studio.tripo3d.ai/workspace/generate/your-model-id"
python convert_tripo.py "C:\path\to\model.glb"
```

## Output

If the input is `model.glb`, the cleaned output becomes:

```text
model_ready.glb
```

The original input file is deleted after a successful conversion.

When the input is a Tripo URL, the script will:

1. Open the page.
2. Capture the `.glb` request.
3. Download the original file into the project folder.
4. Convert it to `_ready.glb`.
5. Delete the downloaded original file.

When the input is a local file, the script will:

1. Convert it to `_ready.glb`.
2. Delete the original file after success.

## Notes

- The script expects the Tripo page to expose the model through browser network requests.
- If the page requires authentication, you may need to add a logged-in Playwright context later.
- The conversion step uses `gltf-transform dequantize` to remove quantization and meshopt compression.
- If the model does not load within the capture window, the script will not find a `.glb` URL.

## Troubleshooting

### Node.js is missing

Install Node.js from https://nodejs.org/ and run the script again.

### Playwright is missing

The script will try to install it automatically. If that fails, run:

```bash
python -m pip install playwright
python -m playwright install chromium
```

### `gltf-transform` is missing

The script will try to install it automatically with:

```bash
npm install -g @gltf-transform/cli
```

### No `.glb` URL was found

- Confirm the Tripo page finishes loading the model.
- Try a different workspace URL.
- If the model appears only after extra interaction, the capture window may need to be extended.

## License

No license has been specified yet.
