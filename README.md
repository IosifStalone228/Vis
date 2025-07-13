# JBI100 Visualization | Group 78

## Overview
This repository contains the source code for the **JBI100 Visualization** project by Group 78. The application provides insightful visualizations using modern tools and can be run locally using Docker.

The visualizations in this project are based on data from the [OSHA Establishment-Specific Injury and Illness Data](https://www.osha.gov/Establishment-Specific-Injury-and-Illness-Data).

---

## Project Structure

The project directory includes the following key files and folders:

1. `datasets/processed_data.parquet`: Preprocessed data file containing establishment-specific injury and illness information used for visualizations.

2. `notebooks/`: Jupyter notebooks for data exploration, preprocessing, and analysis during the project development phase.

3. `src/layouts.py`: Defines the layout and structure of the Dash web application, including the arrangement of visualizations and UI components.

4. `src/data.py`: Contains functions and logic for data processing, filtering, and computation of metrics required for visualizations.

5. `src/mappings.py`: Provides mappings for dropdown menu options, state abbreviations, and KPI labels for consistent usage across the application.

6. `src/visualizations.py`: Implements functions for generating visualizations like radar charts, treemaps, scatter plots, and stacked bar charts using Plotly.

7. `application.py`: Entry point for the application, where the Dash server is initialized, layouts are applied, and callbacks are registered.

8. `Dockerfile`: Contains instructions to build a Docker image for the application, ensuring consistent runtime environments.

9. `README.md`: Project documentation including an overview, setup instructions, and guidelines for contributors.

10. `LICENSE`: Licensing details for the project, outlining usage permissions under the MIT License.

11. `requirements.txt`: Lists Python dependencies required to run the application, ensuring all necessary libraries are installed in the environment.


## How to Launch the Application Locally

Follow these steps to set up and run the application:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/gladkykhse/jbi100-visualization-group78.git
   ```

2. **Navigate to the project directory:**

   ```bash
   cd jbi100-visualization-group78
   ```

3. **Build the Docker image:**

   ```bash
   docker build -t dashboard-app .
   ```

4. **Run the application:**

   ```bash
   docker run -p 8080:8080 dashboard-app
   ```

5. Open your web browser and go to `http://localhost:8080` to access the application.

## Running the Project Locally Without Docker

To run the project locally without Docker, ensure you have Python 3.10 or higher installed on your system and follow these steps:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/gladkykhse/jbi100-visualization-group78.git
   ```

2. **Navigate to the Project Directory**
   
   ```bash
   cd jbi100-visualization-group78
   ```

3. **Set Up a Virtual Environment (Optional)**
   
   ```bash
   python -m venv venv
   source venv/bin/activate    # On macOS/Linux
   venv\Scripts\activate       # On Windows
   ```
   
3. **Install Dependencies**
   
   ```bash
   pip install -r requirements.txt
   ```
   
3. **Run the Application**
   
   ```bash
   python application.py
   ```

## Contributing
Feel free to submit issues or pull requests to contribute to this project.

## License
This project is licensed under the MIT License. See the LICENSE file for details.