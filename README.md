# Bias in Perceived Creativity of AI Artwork

**Author:** Connor McKelvey  
**Project:** Final Research Project for UGS 303 Being Creative, The University of Texas at Austin (Fall 2025)

---

### Table of Contents
1.  [Introduction](#introduction)
2.  [Primary Research Question](#primary-research-question)
3.  [Methodology](#methodology)
4.  [Summary of Findings](#summary-of-findings)
5.  [Discussion](#discussion)
6.  [Project Links & Resources](#project-links--resources)
7.  [Codebase Overview](#codebase-overview)
8.  [Physical Robot Arm Design](#physical-robot-arm-design)
9.  [AI Usage Disclosure](#ai-usage-disclosure)

---

## Introduction

Following the rapid advancement and public release of powerful generative artificial intelligence (AI), systems now demonstrate the ability to produce artwork, music, and writing that rivals human output. This technological leap raises a fundamental question: **Do people perceive human-made creative works as inherently more creative than AI-generated works when the source is revealed?**

This study investigates this question from the perspective of creativity science. Understanding this potential bias is critical, because if humans systematically favor human creators, AI-generated works may be undervalued despite their technical sophistication or aesthetic appeal. The study defines creativity consistent with Runco and Jaeger's standard definition: requiring both **originality** and **effectiveness**. The project explores whether the common hostility toward AI art, often framed around concerns of plagiarism, stems from a deeper discomfort with machine creativity itself.

## Primary Research Question

> **Does knowledge of the creator (human versus AI) affect the perceived creativity of visual images?**

## Methodology

To address the research question, this study focused on rigorous stimulus standardization and a counterbalanced presentation design.

#### Overview & Procedure
*   **Platform:** An anonymous online survey was built using Qualtrics.
*   **Task:** Participants were presented with two images side-by-side and asked to rate their creativity on a **1-7 Likert scale**.
*   **Structure:** The survey was split into two blocks separated by demographic questions to reduce carryover effects.
    *   **Block 1:** Presented five pairs of images with **no source labels**.
    *   **Block 2:** Presented five different pairs of images correctly labeled as **“Human Made”** or **“AI Made”**.
*   **Counterbalancing:** To prevent image memorization, two versions of the survey were used. Participants were randomly assigned to a version where the labeled and unlabeled image sets were swapped.

#### Stimulus Design
The most critical aspect of the methodology was standardizing the visual stimuli to ensure that ratings were based on perceived creativity, not on confounding variables like style, complexity, or medium.

*   **Style:** Semi-abstract monochromatic line art was used to make AI and human works nearly indistinguishable without labels.
*   **Sourcing:**
    *   **Human Art:** Sourced from Dribbble.com, a platform for professional artists.
    *   **AI Art:** Generated on Recraft.ai using text prompts adapted from the descriptions of the human-made art.
*   **Standardization Process:**
    1.  All images were converted to SVGs (Scalable Vector Graphics).
    2.  Custom Python scripts converted the SVGs into a series of (X, Y) coordinates.
    3.  The coordinate paths were simplified using the **Ramer-Douglas-Peucker algorithm** to quantify and balance the complexity of each image pair (see Figure 3 in the full paper).
    4.  The final stimuli were generated from a **simulation of a two-jointed robot drawing arm**, ensuring that all images were presented in an identical, algorithmic style.

## Summary of Findings

The analysis was performed on 27 complete responses. The results show a statistically significant difference in how AI-generated art is perceived when its source is revealed.

#### Descriptive Statistics
| Group | Number of Ratings (n) | Mean Rating (1-7) | Standard Deviation |
| :--- | :--- | :--- | :--- |
| Unlabeled Human | 134 | 3.80 | 1.39 |
| **Unlabeled AI** | 135 | **4.50** | 1.44 |
| Labeled Human | 134 | 3.75 | 1.31 |
| **Labeled AI** | 133 | **4.02** | 1.43 |

#### Statistical Significance (t-tests)
| Comparison | t-statistic | p-value | Statistically Significant? |
| :--- | :--- | :--- | :--- |
| Unlabeled Human vs Unlabeled AI | -4.049 | 0.0001 | **Yes** |
| **Labeled AI vs Unlabeled AI** | **2.705** | **0.0073** | **Yes** |
| Unlabeled Human vs Labeled Human | 0.317 | 0.7517 | No |

**Conclusion:** The null hypothesis—that labeling has no effect—is **rejected**. Labeling an artwork as AI-generated significantly decreases its perceived creativity rating (from a mean of 4.50 to 4.02).

## Discussion

The results are particularly noteworthy: a statistically significant negative bias against AI creativity was found, even among a participant pool of young individuals who frequently use generative AI tools. This outcome aligns with existing research on anthropocentric bias (e.g., Kim and Kim, 2023) and suggests that even as society adopts AI as a tool, a fundamental resistance to accepting machine creativity persists.

For the field of computer and robotics engineering, this perception bias presents a significant challenge. It raises a critical question for the future of human-computer interaction: will this skepticism foster necessary critical oversight, or will it cause genuinely creative AI solutions to be prematurely dismissed?

## Project Links & Resources

This repository contains all data, code, and information related to this project.
*   **[Qualtrics Survey](https://utexas.qualtrics.com/jfe/form/SV_9ZT9N2LNVsxPjDw)** (Randomly assigns user to version A or B)
*   **[Drawing Robot Simulator Website](https://connormmckelvey.github.io/Being-Creative-Research-Project/index.html)**
*   **[Full Research Paper PDF](Complete_Paper_Bias_in_Perceived_Creativity_of_AI_Artwork.pdf)**: For detailed explanations, equations, and a complete Works Cited list.

## Codebase Overview

The source code is located in the `src` folder and is organized into several Python files.

*   `main.py`: The main Python file that implements helper functions and organizes them for easy use.
*   `survey_data_analysis.py`: Reads the specified dataset and prints the full statistical analysis seen in the paper.
*   `svg_to_xy.py`: Helper script to convert SVG path data into a list of (X, Y) coordinates.
*   `xy_to_angles_inverse_kinematics.py`: Implements the inverse kinematics equations to convert coordinates into robot arm angles.
*   `command_generator.py`: Converts angle data into command files for the simulator or physical robot.
*   `main.cpp`: The Arduino code for controlling the physical robot arm (see below). Not used in the final survey.

## Physical Robot Arm Design

The original project goal was to have a physical two-jointed robot arm draw all stimuli to achieve maximum standardization. Due to time constraints, this was shifted to a simulation. The physical arm was built using 3D printed parts from Texas Invention Works and is controlled by an Arduino Uno. The design and code are included in this repository as a supplemental part of the project.

## AI Usage Disclosure

Artificial intelligence tools, including ChatGPT and Google Gemini, were used to assist in this research project. Their primary applications were in programming assistance for the inverse kinematics, the simulator website, and the statistical analysis script. They also provided valuable insight into research methods and helped improve grammar and paper structure. All code generated by AI was reviewed, tested, and validated by the author.
