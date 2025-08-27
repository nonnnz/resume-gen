<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/github_username/resume-gen">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">AI-Powered PDF Resume Generator</h3>

  <p align="center">
    A Python script to generate beautiful, multi-lingual PDF resumes from JSON data. This project was largely developed with the assistance of AI, showcasing the power of prompt-based code generation and refactoring.
    <br />
    <a href="https://github.com/github_username/resume-gen"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/github_username/resume-gen/tree/main/resume">View Samples</a>
    &middot;
    <a href="https://github.com/github_username/resume-gen/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/github_username/resume-gen/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://github.com/github_username/resume-gen/tree/main/resume)

This project is a powerful Python script that automates the creation of professional-looking PDF resumes from structured JSON data. It was developed with significant contributions from AI, demonstrating how modern AI tools can accelerate development and build robust applications.

Key Features:
*   **JSON to PDF**: Easily define your resume content in a JSON file.
*   **Multi-Lingual Support**: Built-in support for English and Thai.
*   **Theming**: Choose from multiple themes (`modern`, `classic`, `minimal`) to style your resume.
*   **Smart Text Wrapping**: Automatically wraps text to fit the layout, even for languages without spaces between words.
*   **Automatic Page Breaks**: Content flows seamlessly across multiple pages.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

*   [![Python][Python-shield]][Python-url]
*   [![ReportLab][ReportLab-shield]][ReportLab-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

Follow these steps to set up the project locally.

### Prerequisites

Make sure you have Python 3 and pip installed on your system.
*   Python 3
    ```sh
    # Check your python version
    python --version
    ```
*   pip
    ```sh
    pip --version
    ```

### Installation

1.  Clone the repo
    ```sh
    git clone https://github.com/github_username/resume-gen.git
    cd resume-gen
    ```
2.  Install required Python packages. It's recommended to use a virtual environment.
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
3.  Ensure you have the necessary fonts (`NotoSansThai` and `Sarabun`) in the `fonts/` directory. The script will look for them there.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

To generate resumes, run the script from your terminal. You can process a single JSON object or an array of them from a file.

```sh
python resume_pdf-gpt-refactored.py --data resume_all_extended.json --theme modern --outdir resume
```

### Command-line Arguments:
*   `--data`: Path to the input JSON file.
*   `--theme`: The visual theme to use (`modern`, `classic`, `minimal`).
*   `--outdir`: The directory to save the generated PDF files.

_For more examples, please refer to the [sample JSON files](https://github.com/github_username/resume-gen) like `resume_all_extended.json` and `resume_all_extended_th.json`._

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

- [ ] Add more themes and customization options.
- [ ] Support for more languages.
- [ ] Add a simple web UI for generating resumes.
- [ ] Package the script for easier distribution (e.g., via PyPI).

See the [open issues](https://github.com/github_username/resume-gen/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Contact

Your Name - @your_twitter - your_email@example.com

Project Link: [https://github.com/github_username/resume-gen](https://github.com/github_username/resume-gen)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

*   [Best-README-Template](https://github.com/othneildrew/Best-README-Template)
*   [ReportLab](https://www.reportlab.com/)
*   [Noto Fonts](https://fonts.google.com/noto)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/github_username/resume-gen.svg?style=for-the-badge
[contributors-url]: https://github.com/github_username/resume-gen/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/github_username/resume-gen.svg?style=for-the-badge
[forks-url]: https://github.com/github_username/resume-gen/network/members
[stars-shield]: https://img.shields.io/github/stars/github_username/resume-gen.svg?style=for-the-badge
[stars-url]: https://github.com/github_username/resume-gen/stargazers
[issues-shield]: https://img.shields.io/github/issues/github_username/resume-gen.svg?style=for-the-badge
[issues-url]: https://github.com/github_username/resume-gen/issues
[license-shield]: https://img.shields.io/github/license/github_username/resume-gen.svg?style=for-the-badge
[license-url]: https://github.com/github_username/resume-gen/blob/master/LICENSE.txt
[product-screenshot]: images/screenshot.png
[Python-shield]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[ReportLab-shield]: https://img.shields.io/badge/ReportLab-A40000?style=for-the-badge&logo=reportlab&logoColor=white
[ReportLab-url]: https://www.reportlab.com/
