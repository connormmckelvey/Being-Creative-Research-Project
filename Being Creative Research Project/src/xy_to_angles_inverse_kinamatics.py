import math

def radians_to_degrees(rad):
    """
    Convert radians to degrees.

    Parameters:
    rad (float): Angle in radians.

    Returns:
    float: Angle in degrees.
    """
    return rad * (180.0 / math.pi)

def compute_joint_angles(x, y, l1, l2):
    """
    Compute the joint angles (thetas) for a 2D planar robotic arm given the end-effector position (x, y)
    and the lengths of the two arm segments (l1, l2).

    Parameters:
    x (float): The x-coordinate of the end-effector.
    y (float): The y-coordinate of the end-effector.
    l1 (float): The length of the first arm segment.
    l2 (float): The length of the second arm segment.

    Returns:
    tuple: A tuple containing the two joint angles (shoulder (theta1), elbow (theta2)) in radians.
    """
    if x is None and y is None:
        return (None, None)
    
    return (radians_to_degrees(calculate_shoulder_theta(x, y, l1, l2)),
            radians_to_degrees(calculate_elbow_theta(x, y, l1, l2)))

def calculate_shoulder_theta(x, y, L1, L2):
    """
    Calculate the shoulder joint angle (theta1) for a 2D planar robotic arm given the end-effector position (x, y)
    and the lengths of the two arm segments (L1, L2).

    Parameters:
    x (float): The x-coordinate of the end-effector.
    y (float): The y-coordinate of the end-effector.
    L1 (float): The length of the first arm segment.
    L2 (float): The length of the second arm segment.

    Returns:
    float: The shoulder joint angle (theta1) in radians.
    """
    r = math.sqrt(x**2 + y**2)

    if r < abs(L1 - L2):
        raise ValueError("The point ({}, {}) is not reachable with arm lengths {} and {}".format(x, y, L1, L2))

    cos_theta2 = (r**2 - L1**2 - L2**2) / (2 * L1 * L2)
    theta2 = math.acos(cos_theta2)

    k1 = L1 + L2 * cos_theta2
    k2 = L2 * math.sin(theta2)
    theta1 = math.atan2(y, x) - math.atan2(k2, k1)

    return theta1

def calculate_elbow_theta(x, y, L1, L2):
    """
    Calculate the elbow joint angle (theta2) for a 2D planar robotic arm given the end-effector position (x, y)
    and the lengths of the two arm segments (L1, L2).

    Parameters:
    x (float): The x-coordinate of the end-effector.
    y (float): The y-coordinate of the end-effector.
    L1 (float): The length of the first arm segment.
    L2 (float): The length of the second arm segment.

    Returns:
    float: The elbow joint angle (theta2) in radians.
    """
    r = math.sqrt(x**2 + y**2)

    if r < abs(L1 - L2):
        raise ValueError("The point ({}, {}) is not reachable with arm lengths {} and {}".format(x, y, L1, L2))

    cos_theta2 = (r**2 - L1**2 - L2**2) / (2 * L1 * L2)
    theta2 = math.acos(cos_theta2)

    return theta2