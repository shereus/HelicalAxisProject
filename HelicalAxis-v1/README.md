# Script README

This script is an attempt and work in progress to read motion data from a CSV file, calculate the finite helical axis (FHA) of knee motion, and visualizes it using a 3D plot.

## Prerequisites
- Python 3.x
- NumPy
- Matplotlib
- Pandas

## Usage

1. Make sure the required Python packages are installed.

2. Set the file path and name in the script:

   ```python
   path = './test_data/IMU_test_data/'
   filename = '90deg_z.csv'
   ```

   Update `path` and `filename` variables to match the location and name of your IMU test data file.

3. Run the script using the Python interpreter.

   ```
   python script_name.py
   ```

4. The script will read the CSV file and perform the following steps:

   - Convert quaternions to rotation matrices.
   - Calculate the finite helical axis (FHA) of knee motion using the provided quaternions.
   - Normalize the FHA vectors.
   - Generate a 3D plot showing the FHA vectors.

5. The 3D plot will be displayed, allowing you to visualize the FHA of the knee motion.

## Notes

- Ensure that the CSV file contains the required columns: `Time`, `w1`, `x1`, `y1`, `z1`, `w2`, `x2`, `y2`, `z2`. 

- The script uses the `quaternion_to_rotation_matrix` function to convert quaternions to rotation matrices. If you have a different method for converting quaternions, you can modify this function accordingly.

- The FHA vectors are plotted in the 3D plot. You can customize the plot appearance or modify the plotting code according to your preferences.

- Make sure the required libraries (NumPy, Matplotlib, Pandas) are installed in your Python environment. If any of the libraries are missing, you can install them using `pip`:

  ```
  pip install numpy matplotlib pandas
  ```

- This script assumes that the provided IMU test data file is in a CSV format and contains valid quaternion values.

- Adjust the plot labels and styling as needed to suit your requirements.

## License

This script is provided under the [MIT License](https://opensource.org/licenses/MIT). Feel free to modify and use it according to your needs.

## Acknowledgments

This script utilizes the following libraries:

- NumPy: https://numpy.org/
- Matplotlib: https://matplotlib.org/
- Pandas: https://pandas.pydata.org/

The finite helical axis (FHA) calculation algorithm is based on relevant research and mathematical principles.