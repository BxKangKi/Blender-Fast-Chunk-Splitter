# Blender-Fast-Chunk-Splitter

## Fast Chunk Splitter for Blender

An ultra-fast, dependency-free Blender add-on that splits large meshes into a precise X/Y grid of chunks. Built specifically for performance, it utilizes Blender's native **NumPy** and **BMesh** to slice geometry without freezing your system or causing memory overflows.

## Why This Add-on?
Previous versions of chunk splitters relied on heavy external Python libraries (like `trimesh`) and unstable multiprocessing that often caused Blender to crash or leave zombie processes. 

This version has been completely rewritten to be **100% native to Blender**. By utilizing NumPy for AABB (Axis-Aligned Bounding Box) early rejection, the add-on mathematically scans the entire mesh in milliseconds and entirely skips empty spaces, making it exponentially faster than traditional slicing methods.

## Features
- **Zero Dependencies:** No need to install `pip`, external modules, or background workers. Just install the `.zip` and go.
- **NumPy Early Rejection:** Analyzes 1,000,000+ polygons in a fraction of a second to skip empty chunks, massively boosting speed.
- **Two Slicing Modes:** Choose between high-speed hollow slicing and watertight solid slicing.
- **Crash-Proof:** Runs entirely within Blender's native Python environment, ensuring stable memory usage.

## Installation
1. Click the green **[ <> Code ]** button at the top right of this repository.
2. Select **[ Download ZIP ]** (Do not extract the `.zip` file).
3. Open Blender and go to `Edit > Preferences > Add-ons`.
4. Click **[ Install... ]** at the top right and select the downloaded `.zip` file.
5. Check the box next to **Object: Fast Chunk Splitter** to enable it.

## How to Use
1. Select the **Mesh object** you want to split in the 3D Viewport.
2. Press the **`N`** key to open the right sidebar and navigate to the **Chunk Splitter** tab.
3. Set the grid size by adjusting the **X Chunks** and **Y Chunks** sliders.
4. Choose your preferred **Mode**:
   - **Bisect Only (Hollow):** Uses BMesh slicing. Extremely fast and memory-efficient. Leaves the cut sides hollow. Ideal for massive environments or landscapes.
   - **Solid (Fill Sides):** Uses the Boolean modifier. Slower and requires more RAM, but caps the holes to create completely solid, watertight chunks.
5. Click **`Execute Fast Split`**. 

The original mesh will be hidden, and a new collection named `[ObjectName]_Chunks` will be created containing all the perfectly sliced pieces.

## 💻 Compatibility
- Requires **Blender 3.0** or higher.
- Compatible with Windows, macOS, and Linux out of the box.
