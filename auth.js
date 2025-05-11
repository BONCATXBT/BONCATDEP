// auth.js
const CONFIG = {
    TOKEN_MINT_ADDRESS: 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
    REQUIRED_TOKEN_AMOUNT: 0 * 10 ** 6, // 6 decimals
    SERVER_URL: 'https://zork.onrender.com',
    MAIN_PAGE: 'index.html', // Redirect to this page if access is denied
  };
  
  let walletAddress = localStorage.getItem('walletAddress') || null;
  let connection = null;
  
  function appendLog(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
  }
  
  async function checkTokenBalance(publicKey) {
    try {
      const response = await fetch(`${CONFIG.SERVER_URL}/api/check-token-balance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          publicKey: publicKey,
          tokenMintAddress: CONFIG.TOKEN_MINT_ADDRESS,
        }),
      });
  
      if (!response.ok) throw new Error(`Server responded with status: ${response.status}`);
      const data = await response.json();
      if (data.error) {
        appendLog(`Server error checking token balance: ${data.error}`, 'error');
        return 0;
      }
  
      appendLog(`Token balance received: ${data.balance}`, 'success');
      return data.balance || 0;
    } catch (error) {
      appendLog(`Error checking token balance: ${error.message}`, 'error');
      return 0;
    }
  }
  
  async function connectWallet() {
    if (!window.solana || !window.solana.isPhantom) {
      appendLog('Phantom Wallet not detected.', 'error');
      return false;
    }
  
    try {
      const resp = await window.solana.connect();
      walletAddress = resp.publicKey.toString();
      localStorage.setItem('walletAddress', walletAddress);
      appendLog(`Wallet connected: ${walletAddress}`, 'success');
  
      connection = new window.solanaWeb3.Connection(window.solanaWeb3.clusterApiUrl('mainnet-beta'), 'confirmed');
      const tokenBalance = await checkTokenBalance(walletAddress);
  
      if (tokenBalance >= CONFIG.REQUIRED_TOKEN_AMOUNT) {
        appendLog(`Access granted! User holds ${tokenBalance / 10 ** 6} MORVOXBT tokens.`, 'success');
        return true;
      } else {
        appendLog(`Access denied. User holds ${tokenBalance / 10 ** 6} MORVOXBT tokens, but 1,000,000 are required.`, 'warning');
        return false;
      }
    } catch (err) {
      appendLog(`Wallet connection error: ${err.message}`, 'error');
      return false;
    }
  }
  
  async function enforceAuth() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    if (currentPage === CONFIG.MAIN_PAGE) {
      return;
    }
  
    // Hide main content and show loading message
    const mainContent = document.getElementById('mainContent');
    const loadingMessage = document.getElementById('loadingMessage');
    if (mainContent) {
      mainContent.style.display = 'none';
    }
    if (loadingMessage) {
      loadingMessage.style.display = 'block';
    }
  
    // Check wallet and token balance
    const hasAccess = await connectWallet();
    if (!hasAccess) {
      window.location.href = `/${CONFIG.MAIN_PAGE}`;
    } else {
      if (mainContent) {
        mainContent.style.display = 'block';
      }
      if (loadingMessage) {
        loadingMessage.style.display = 'none';
      }
    }
  }
  
  // Run the auth check when the page loads
  document.addEventListener('DOMContentLoaded', enforceAuth);