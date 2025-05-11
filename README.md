# BONCATXBT Framework

**BONCATXBT** is a futuristic web-based interface for interacting with the `$BONCAT` meme coin ecosystem on the Solana blockchain. Powered by the GORK AI model, this application provides a terminal-style chat interface where users can interact with BONCATXBT, a sassy crypto cat AI. The project features a visually engaging intro page with a 3D globe animation, a professional loading sequence, and a full-screen terminal for chatting with the AI.

## Features

- **Intro Page with 3D Globe Animation**: A visually stunning intro page featuring a Three.js-powered wireframe globe with pulsing effects and orbiting rings, welcoming users to the BONCATXBT framework.
- **Solana Wallet Integration**: Connect your Solana wallet (e.g., Phantom) to access the terminal. Wallet connection is required to proceed.
- **Professional Loading Sequence**: A high-tech loading page with system logs, a spinner, and a progress bar, simulating an AI boot sequence.
- **Terminal Interface**: A full-screen terminal where users can chat with BONCATXBT, a humorous and memetic AI that provides insights, lore, and sass about the `$BONCAT` ecosystem.
- **Neon Green Cyberpunk Aesthetic**: The UI uses a black background with neon green accents, glitch effects, and a 'Roboto Mono' font for a retro-futuristic vibe.
- **Responsive Design**: The layout adapts to different screen sizes, ensuring a seamless experience on desktops, tablets, and mobile devices.

## Prerequisites

To run this project, you need the following:

- A modern web browser (e.g., Chrome, Firefox, Edge).
- A Solana wallet extension (e.g., [Phantom Wallet](https://phantom.app/)) installed in your browser.
- An internet connection (the app fetches data from external APIs and uses CDN-hosted libraries).

## Setup

1. **Clone or Download the Repository**:
   - Clone this repository to your local machine:
     ```bash
     git clone <repository-url>
     ```
   - Alternatively, download the ZIP file and extract it.

2. **Directory Structure**:
   Ensure the following files are present in the root directory:
   - `index.html`: The main HTML file containing the application.
   - `logo.png`: The logo image displayed on the intro page (optional; you can replace it with your own logo).

3. **Dependencies**:
   - The project uses CDN-hosted libraries, so no local installation is required. The following libraries are included:
     - **Solana Web3.js** (`@solana/web3.js@1.95.3`): For Solana wallet integration.
     - **Three.js** (`three.js@r134`): For the 3D globe animation on the intro page.
     - **Google Fonts** (`Roboto Mono`): For the terminal-style typography.

4. **Host the Application**:
   - Since this is a static web application, you can host it using any web server. For local development, you can use a simple HTTP server like Python's `http.server`:
     ```bash
     python -m http.server 8000
     ```
   - Alternatively, open `index.html` directly in your browser for testing (note: some features, like wallet connection, may require a server due to CORS restrictions).

## Usage

1. **Open the Application**:
   - Navigate to `http://localhost:8000` (or the URL where your server is running) in your browser.
   - If you opened `index.html` directly, use `file://` path, but prefer a server for full functionality.

2. **Connect Your Wallet**:
   - The intro page displays a 3D globe animation, a "Connect Wallet" button, and an access message.
   - Click the "Connect Wallet" button to connect your Solana wallet (e.g., Phantom).
   - If successful, the intro page will fade out, and a loading sequence will begin.

3. **Loading Sequence**:
   - After wallet connection, a loading page appears, simulating an AI boot sequence with system logs, a spinner, and a progress bar.
   - This sequence lasts approximately 4.5 seconds before transitioning to the terminal.

4. **Interact with BONCATXBT**:
   - Once the terminal loads, you'll see a greeting from BONCATXBT, the "sassiest crypto cat on Solana."
   - Type your message in the textarea and press "Send" (or hit Enter) to chat with the AI.
   - BONCATXBT responds with humor, `$BONCAT` lore, and blockchain insights, powered by the GORK AI model.

## Project Structure

- **HTML**:
  - `index.html`: Contains the main structure, including the intro page, loading page, and terminal interface.
- **CSS**:
  - Embedded in `index.html` within a `<style>` tag.
  - Defines the neon green cyberpunk aesthetic, animations (glitch, flicker, pulse), and responsive layouts.
- **JavaScript**:
  - Embedded in `index.html` within a `<script>` tag.
  - Handles wallet connection, Three.js globe animation, terminal chat functionality, and API interactions with xAI's chat completions endpoint.
- **Assets**:
  - `logo.png`: Placeholder for the BONCATXBT logo (optional; not used in the current version with the globe animation).

## Customization

- **Globe Animation**:
  - Modify the `.intro-globe` class in the CSS to change the size of the globe animation.
  - Adjust the Three.js parameters in the JavaScript (e.g., sphere geometry, rotation speed, colors) to customize the animation.
- **Colors and Fonts**:
  - Update the neon green colors (`#00FF00`, `#00CC00`) in the CSS to change the theme.
  - Replace 'Roboto Mono' with another font by updating the Google Fonts import and CSS.
- **Loading Sequence**:
  - Change the duration of the loading sequence by adjusting the `load` animation duration in the CSS and the corresponding timeout in the JavaScript.
  - Edit the `.log-message` text in the HTML to customize the boot sequence messages.

## Known Issues

- **Wallet Connection**:
  - Requires a Solana wallet extension (e.g., Phantom) to be installed. Without it, an error message will be displayed.
  - Some features may not work if `index.html` is opened directly (`file://`) due to CORS restrictions; use a local server instead.
- **API Key**:
  - The xAI API key is hardcoded in the script for demonstration purposes. In a production environment, secure the API key using environment variables or a backend proxy.

## Future Improvements

- **Secure API Key Handling**:
  - Move the xAI API key to a backend server or environment variable to enhance security.
- **Enhanced Animations**:
  - Add more animations (e.g., glitch effects on the globe, floating glyphs) to the intro page for a richer experience.
- **Chat Features**:
  - Implement message history persistence using local storage.
  - Add support for more interactive commands in the terminal.
- **Accessibility**:
  - Improve accessibility by adding ARIA labels and keyboard navigation support.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Three.js](https://threejs.org/) for 3D animations.
- Uses [Solana Web3.js](https://solana-labs.github.io/solana-web3.js/) for wallet integration.
- Powered by [xAI's GORK AI model](https://x.ai/) for chat functionality.
- Inspired by cyberpunk and retro-futuristic aesthetics.

## Contact

For questions, feedback, or contributions, please open an issue on this repository or contact the maintainers.

---
Happy memeing with BONCATXBT! 🚀