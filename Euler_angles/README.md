## Euler_angles.py README

This script is designed to process motion data from IMU sensors and calculate the angular differences between the sensor orientations. It also includes functionality to convert quaternions to Euler angles and create plots for visualization.

### Usage

1. Update the `path` variable with the directory path where your data file is located.
2. Update the `filename` variable with the name of your data file.
3. Run the script.

### Dependencies

The script requires the following dependencies to be installed:

- `math`
- `scipy`
- `pandas`
- `numpy`
- `csv`
- `matplotlib`

You can install these dependencies using the package manager of your choice (e.g., `pip`).

### Output

The script generates several plots to visualize the sensor orientations and angular differences. The plots include:

- Sensor 1 Euler angles (zyx sequence)
- Sensor 2 Euler angles (zyx sequence)
- Angular differences between the sensors (xyz sequence)
- Inverted angular differences between the sensors (xyz sequence)

Additionally, the script writes the processed data to a new CSV file with an adjusted filename, appending "_xyz-sequence" to the original filename. The CSV file includes the following columns:

- Time
- Sensor 1 Euler angles (X, Y, Z)
- Sensor 2 Euler angles (X, Y, Z)
- Angular differences (x, y, z)
- Inverted angular differences (x, y, z)

### Note

Please ensure that the input data file is in the correct format and contains the necessary columns: 'Time', 'w1', 'x1', 'y1', 'z1', 'w2', 'x2', 'y2', 'z2'.