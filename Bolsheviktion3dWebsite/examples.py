#!/usr/bin/env python3

import struct
import time
import os
import random
import sys
import zipfile
import io
import logging

from flask_mail import Mail, Message

logger = logging.getLogger(__name__)


USER_COUNTER = 0  # Simple global counter -- This needs to be saved for persistence.

LETTER_1 = (
    "30 July, Sunday. Today dear Alexei turned 13. May the Lord grant him health, "
    "patience, and strength of spirit and body in our present trying times! We went "
    "to Mass and after breakfast to prayers, where we brought the icon of the "
    "Znamenskaya Mother of God. Somehow it felt especially warm to pray to her holy "
    "face with all our people. Everything is packed, and only paintings remain on the walls."
)
LETTER_2 = (
    "The house is fine, clean. We have been assigned 4 rooms: a corner bedroom, a "
    "lavatory, next door a dining room with windows onto a little garden and a view "
    "of a low-lying part of town, and finally, a spacious hall with arches in place "
    "of doors. We arranged ourselves in the following manner: Alix, Marie, and I "
    "together in the bedroom. A shared lavatory. Demidova in the dining room, and "
    "in the hall—Botkin, Chemodurov, and Sednev. In order to get to the washroom and "
    "water closet one must go past the sentry. A very high wooden fence has been built "
    "around the house 2 sazhens from the windows: a chain of sentries has been posted "
    "there and in the little garden too."
)

# Pre-calculate these so we know exactly how many bytes to read in our C code or verify function.
LETTER_1_BYTES = LETTER_1.encode("utf-8")
LETTER_2_BYTES = LETTER_2.encode("utf-8")

LETTER_1_SIZE = len(LETTER_1_BYTES)
LETTER_2_SIZE = len(LETTER_2_BYTES)

def create_registration_b3d(username: str, email: str):
    """
    Creates a .b3d file in memory using a buffer.
    """
    global USER_COUNTER
    USER_COUNTER += 1

    username_bytes = username.encode("utf-8")
    username_length = len(username_bytes)

    pattern = [1, 4, 8, 8]
    pattern_index = 0

    # Build the username section
    username_section = bytearray()

    # 4-byte length
    username_section += struct.pack("<i", username_length)

    # Then each char + junk
    for char in username_bytes:
        junk_size = pattern[pattern_index]
        pattern_index = (pattern_index + 1) % len(pattern)

        # The actual character
        username_section.append(char)

        # Junk bytes: random bits of 0 or 1
        for _ in range(junk_size):
            bits_str = "".join(str(random.randint(0, 1)) for _ in range(8))
            byte_val = int(bits_str, 2)
            username_section.append(byte_val)

    # Create an in-memory buffer for the .b3d file
    b3d_buffer = io.BytesIO()

    # Write content to the buffer
    b3d_buffer.write(b"BN3D")  # 1) Magic header
    atomic_time = int(time.time())
    b3d_buffer.write(struct.pack("<Q", atomic_time))  # 2) Atomic time
    b3d_buffer.write(struct.pack("<Q", USER_COUNTER))  # 3) Internal user counter
    b3d_buffer.write(LETTER_1_BYTES)  # 4) Letter 1
    b3d_buffer.write(username_section)  # 5) Username section
    b3d_buffer.write(LETTER_2_BYTES)  # 6) Letter 2

    # Reset the buffer's position to the beginning
    b3d_buffer.seek(0)

    logger.info(f"Created in-memory .b3d file for username '{username}'")
    return b3d_buffer
  
def zip_b3d_file(b3d_buffer: io.BytesIO, static_folder: str):
    """
    Zips the .b3d file and a readme.txt file into an in-memory ZIP file.

    Args:
        b3d_buffer (io.BytesIO): The in-memory .b3d file buffer.
        static_folder (str): Path to the folder containing the registration_b3d_file.txt file.

    Returns:
        io.BytesIO: An in-memory ZIP file containing registration.b3d and readme.txt.
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add the .b3d file to the ZIP archive
        zipf.writestr("registration.b3d", b3d_buffer.read())

        # Add the readme.txt file from the static folder
        readme_path = os.path.join(static_folder, "registration_b3d_file.txt")
        if os.path.exists(readme_path):
            with open(readme_path, "r") as readme_file:
                zipf.writestr("readme.txt", readme_file.read())
        else:
            raise FileNotFoundError(f"{readme_path} not found in the static folder.")

    zip_buffer.seek(0)  # Reset for sending
    logger.info("Created in-memory ZIP file with .b3d and readme.txt")
    return zip_buffer


def send_registration_email(mail, to_email, subject, body, zip_buffer, filename="registration.zip"):
    """
    Sends an email with a ZIP file attachment.

    Args:
        mail - the mail object that will mail to the address.
        to_email (str): Recipient's email address.
        subject (str): Email subject.
        body (str): Email body.
        zip_buffer (io.BytesIO): ZIP file to attach.
        filename (str): Name of the attached file.
    """
    try:
        # Create the email message
        msg = Message(subject=subject, recipients=[to_email])
        msg.body = body

        # Attach the ZIP file
        zip_buffer.seek(0)  # Ensure the buffer is at the start
        msg.attach(filename, "application/zip", zip_buffer.read())

        # Send the email
        mail.send(msg)
        logger.info("Registration email sent successfully")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
