import re

import plotext as plt


def ascii_histogram(data: list) -> str:
    """
    Create an ASCII histogram from a list of data.
    """
    # Create horizontal bar chart with plotext
    plt.clear_figure()

    # Disable colors/styling to prevent ANSI escape codes
    plt.theme("clear")

    plt.bar(
        data,
        orientation="horizontal",
        width=0.6,  # Adjust bar width for better spacing
    )

    # Remove axes and gridlines for cleaner look
    plt.interactive(False)
    plt.theme("clear")

    # Add simple labels
    plt.plotsize(60, len(data) + 4)  # Adjust plot size based on number of clusters

    # Build and display the chart
    chart = plt.build()
    plt.clear_figure()

    # Strip any remaining ANSI escape sequences if needed
    cleaned_chart = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", chart)

    return "\n" + cleaned_chart
