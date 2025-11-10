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
    if x is None or y is None:
        return (None, None)
    try:
        elbow_angle = math.acos((x**2 + y**2 - l1**2 - l2**2) / (2 * l1 * l2))
        elbow_angle = radians_to_degrees(elbow_angle)
        elbow_angle += 90.0  # Adjust for servo mapping

        shoulder_angle = math.atan2(y, x) - math.atan2(l2 * math.sin(math.radians(elbow_angle - 90.0)), l1 + l2 * math.cos(math.radians(elbow_angle - 90.0)))
        shoulder_angle = radians_to_degrees(shoulder_angle)
        return (shoulder_angle, elbow_angle)
    except ValueError as e:
        # This catches "not reachable" errors from the underlying math functions
        print(f"IK Error: {e}")
        return (None, None)
    except Exception as e:
        print(f"An unexpected error occurred during IK: {e}")
        return (None, None)

def old_compute_joint_angles(x, y, l1, l2):
    """
    Compute the joint angles (thetas) for a 2D planar robotic arm given the end-effector position (x, y)
    and the lengths of the two arm segments (l1, l2).

    The shoulder angle (theta1) is calculated relative to the positive X-axis.
    The elbow angle (theta2) is the internal joint angle (which we will map to 90 degrees for straight arm).

    Parameters:
    x (float): The x-coordinate of the end-effector.
    y (float): The y-coordinate of the end-effector.
    l1 (float): The length of the first arm segment.
    l2 (float): The length of the second arm segment.

    Returns:
    tuple: A tuple containing the two joint angles (shoulder (theta1), elbow (theta2)) in degrees, 
           or (None, None) if inputs are None.
    """
    if x is None or y is None:
        return (None, None)
    
    try:
        # Calculate the IK angles in radians
        theta1_rad = calculate_shoulder_theta(x, y, l1, l2)
        theta2_rad = calculate_elbow_theta(x, y, l1, l2)

        # Convert to degrees
        theta1_deg = radians_to_degrees(theta1_rad)
        theta2_deg = radians_to_degrees(theta2_rad)

        # --- Adjustment for Servo Mapping (Crucial step) ---
        
        # 1. Map Shoulder Angle (theta1):
        # The IK provides theta1 relative to the positive X-axis (0 degrees = right).
        # We need to map this to the servo's physical 0-180 range.
        # Since the robot draws in the positive quadrant (0-90 degrees math), 
        # the servo angle will be 90 + (90 - theta1_deg) or similar, depending on the physical mount.
        # Assuming the shoulder servo is mounted such that 0 is Right, 90 is Up:
        # The calculated theta1 must be used directly, but usually mapped from 0-180.
        # In the Quadrant I setup (where 90 deg is UP):
        shoulder_servo_angle = theta1_deg
        
        # 2. Map Elbow Angle (theta2):
        # The IK calculation for theta2 gives the angle between L1 and L2 (0 to 180 degrees).
        # To make the arm straight at the 90-degree servo center:
        # Straight Arm (theta2 = 0) -> Servo 90
        # Folded Arm (theta2 = 180) -> Servo 90 + 90 = 180 (or 90 - 90 = 0)
        # We use a simple mapping where (90 degrees - half the calculated angle)
        
        # This is the knee angle correction required for a 90-degree centered servo:
        # The IK angle (theta2) is 0 to 180, where 0 is fully extended (straight) and 180 is folded.
        # Servo angle = 90 + theta2 (if we use the *exterior* angle)
        # Servo angle = 90 - (theta2_deg - 90) = 180 - theta2_deg (for the 'bent' position)
        
        # The classic SCARA-style IK correction for a 90-degree centered elbow servo:
        # We want theta2=0 (straight) to map to servo=90.
        # The IK formula provides the interior angle (0-180 degrees).
        # Since a straight line is 0 degrees of bend:
        # The required servo angle is 180 - theta2_deg. This works for the "bent under" configuration.
        elbow_servo_angle = 180.0 - theta2_deg

        # The final angle must be constrained to the servo's physical limits (0-180)
        shoulder_servo_angle = max(0.0, min(180.0, shoulder_servo_angle))
        elbow_servo_angle = max(0.0, min(180.0, elbow_servo_angle))


        return (shoulder_servo_angle, elbow_servo_angle)

    except ValueError as e:
        # This catches "not reachable" errors from the underlying math functions
        print(f"IK Error: {e}")
        return (None, None)
    except Exception as e:
        print(f"An unexpected error occurred during IK: {e}")
        return (None, None)


def calculate_shoulder_theta(x, y, L1, L2):
    """
    Calculate the shoulder joint angle (theta1) for a 2D planar robotic arm given the end-effector position (x, y)
    and the lengths of the two arm segments (L1, L2).

    Returns: theta1 in radians.
    """
    r = math.sqrt(x**2 + y**2)

    # Check for reachability and singularity
    if r > (L1 + L2):
        raise ValueError("The point is too far and not reachable (r > L1 + L2).")
    if r < abs(L1 - L2):
        raise ValueError("The point is too close and not reachable (r < |L1 - L2|).")
    if r == 0:
        # Handle the singularity at the origin by pointing straight up (90 deg)
        return math.pi / 2 

    # Law of Cosines to find angle beta (between r and L1)
    cos_beta = (L1**2 + r**2 - L2**2) / (2 * L1 * r)
    # Check for math domain error in acos due to floating point inaccuracies
    if cos_beta > 1.0: cos_beta = 1.0
    if cos_beta < -1.0: cos_beta = -1.0
    
    beta = math.acos(cos_beta)

    # Angle gamma (angle of the wrist relative to the X-axis)
    gamma = math.atan2(y, x)
    
    # theta1 is gamma minus beta (for the 'elbow up' solution)
    theta1 = gamma - beta

    return theta1

def calculate_elbow_theta(x, y, L1, L2):
    """
    Calculate the elbow joint angle (theta2, the interior angle) for a 2D planar robotic arm.

    Returns: theta2 in radians (0 to pi).
    """
    r_squared = x**2 + y**2
    
    if r_squared == 0:
        # Handle singularity at the origin
        return math.pi # 180 degrees (fully folded)

    # Law of Cosines to find the angle theta2 (interior angle between L1 and L2)
    cos_theta2_interior = (r_squared - L1**2 - L2**2) / (2 * L1 * L2)
    
    # Check for math domain error in acos due to floating point inaccuracies
    if cos_theta2_interior > 1.0: cos_theta2_interior = 1.0
    if cos_theta2_interior < -1.0: cos_theta2_interior = -1.0

    # theta2 is the interior angle (0 is straight, 180 is fully folded)
    theta2 = math.acos(cos_theta2_interior)

    return theta2