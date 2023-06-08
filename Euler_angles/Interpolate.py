##### This function can be used to double the amount of data using interpolation #####

def interpolate_quaternions(csv_file):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Extract the necessary columns
    timestamps = df['Time'].values
    quaternions_s1 = df[['w1', 'x1', 'y1', 'z1']].values
    quaternions_s2 = df[['w2', 'x2', 'y2', 'z2']].values

    # Interpolate timestamps
    interpolated_timestamps = np.linspace(timestamps[0], timestamps[-1], len(timestamps) * 2)

    # Interpolate quaternions
    interpolated_quaternions_s1 = np.zeros((len(interpolated_timestamps), 4))
    for i in range(4):
        interpolated_quaternions_s1[:, i] = np.interp(interpolated_timestamps, timestamps, quaternions_s1[:, i])

    interpolated_quaternions_s2 = np.zeros((len(interpolated_timestamps), 4))
    for i in range(4):
        interpolated_quaternions_s2[:, i] = np.interp(interpolated_timestamps, timestamps, quaternions_s2[:, i])

    # Combine timestamps and quaternions
    interpolated_data = np.column_stack((interpolated_timestamps, interpolated_quaternions_s1, interpolated_quaternions_s2))

    return interpolated_data

interpolated_data = interpolate_quaternions(data)
