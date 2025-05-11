const express = require('express');
const axios = require('axios');
const cors = require('cors');
require('dotenv').config(); // ✅ no express-rate-limit here

const app = express();

// Load environment variables
const heliusRpcUrl = process.env.HELIUS_RPC_URL;
const bearerToken = process.env.X_BEARER_TOKEN;
let axiomAuthRefreshToken = process.env.AXIOM_AUTH_REFRESH_TOKEN;
let axiomAuthAccessToken = process.env.AXIOM_AUTH_ACCESS_TOKEN;
let axiomTokenExpiry = Date.now() + 900000;


// Validate required environment variables
if (!heliusRpcUrl) {
  console.error('[ERROR] Missing required environment variable: HELIUS_RPC_URL');
  process.exit(1);
}

if (!axiomAuthRefreshToken || !axiomAuthAccessToken) {
  console.error('[ERROR] Missing required Axiom Trade auth tokens in environment variables');
  process.exit(1);
}

// Configure CORS
app.use(cors({
  origin: (origin, callback) => {
    const allowedOrigins = ['https://zonk.fyi', 'http://localhost:3000', 'http://localhost:5500'];
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

app.use(express.json());

// Logging middleware
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url} from ${req.ip}`);
  next();
});

const TOKEN_MINT_ADDRESS = 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263';

// In-memory storage for signals
let discordSignals = [];
let tokenSentimentSignals = [];
let baseSignals = [];

// Function to refresh the Axiom Trade access token
async function refreshAccessToken() {
  try {
    const response = await axios.post('https://api4.axiom.trade/refresh-access-token', {}, {
      headers: {
        'accept': 'application/json, text/plain, */*',
        'origin': 'https://axiom.trade',
        'referer': 'https://axiom.trade/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Cookie': `auth-refresh-token=${axiomAuthRefreshToken}`
      }
    });

    // Extract cookies
    const cookies = response.headers['set-cookie'] || [];
    let newAccessToken = null;
    let newRefreshToken = null;

    for (const cookie of cookies) {
      if (cookie.includes('auth-access-token')) {
        newAccessToken = cookie.split('auth-access-token=')[1].split(';')[0];
      }
      if (cookie.includes('auth-refresh-token')) {
        newRefreshToken = cookie.split('auth-refresh-token=')[1].split(';')[0];
      }
    }

    if (!newAccessToken) {
      throw new Error('No auth-access-token found in refresh response');
    }

    axiomAuthAccessToken = newAccessToken;
    if (newRefreshToken) {
      axiomAuthRefreshToken = newRefreshToken;
    }

    // Update token expiry (15 minutes from now)
    axiomTokenExpiry = Date.now() + 900000; // 900 seconds = 15 minutes

    console.log('[INFO] Access token refreshed successfully');
    console.log(`[DEBUG] New auth-access-token: ${axiomAuthAccessToken}`);
    console.log(`[DEBUG] New auth-refresh-token: ${axiomAuthRefreshToken}`);
    return true;
  } catch (error) {
    console.error('[ERROR] Failed to refresh Axiom Trade access token:', error.message, error.response?.data || error.stack);
    return false;
  }
}

// Endpoint to get the Axiom access token
app.get('/api/get-axiom-token', async (req, res) => {
  try {
    // Check if the token is expired
    if (Date.now() >= axiomTokenExpiry) {
      console.log('[INFO] Axiom access token expired, refreshing...');
      const success = await refreshAccessToken();
      if (!success) {
        console.error('[ERROR] Failed to refresh Axiom access token');
        return res.status(500).json({ error: 'Failed to refresh Axiom access token' });
      }
    }

    // Return the current access token
    if (!axiomAuthAccessToken) {
      console.error('[ERROR] Axiom access token not available');
      return res.status(500).json({ error: 'Axiom access token not available' });
    }

    console.log('[INFO] Providing Axiom access token to client');
    res.json({ axiomToken: axiomAuthAccessToken });
  } catch (error) {
    console.error('[ERROR] Error in /api/get-axiom-token:', error.message, error.stack);
    res.status(500).json({ error: 'Internal server error', details: error.message });
  }
});

// Token balance endpoint
app.post('/api/check-token-balance', async (req, res) => {
  const { publicKey } = req.body;

  if (!publicKey) {
    console.warn('[WARN] Public key missing in request body');
    return res.status(400).json({ error: 'Public key is required' });
  }

  try {
    const response = await axios.post(heliusRpcUrl, {
      jsonrpc: '2.0',
      id: 1,
      method: 'getTokenAccountsByOwner',
      params: [
        publicKey,
        { programId: 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA' },
        { encoding: 'jsonParsed' }
      ]
    });

    const accounts = response.data.result?.value || [];
    let totalAmount = 0;

    for (const acc of accounts) {
      const info = acc.account?.data?.parsed?.info;
      if (info?.mint === TOKEN_MINT_ADDRESS) {
        totalAmount += Number(info.tokenAmount?.amount || 0);
      }
    }

    console.log(`[INFO] Token balance for ${publicKey}: ${totalAmount}`);
    res.json({ balance: totalAmount });
  } catch (error) {
    console.error('[ERROR] Failed to fetch token accounts:', error.message, error.response?.data || error.stack);
    res.status(500).json({ error: 'Failed to fetch token balance', details: error.message });
  }
});

// X API endpoint
app.get('/api/user/:username', async (req, res) => {
  try {
    const username = req.params.username;
    if (!username) {
      console.warn('[WARN] Username missing in request');
      return res.status(400).json({ error: 'Username is required' });
    }

    const user = await axios.get(`https://api.x.com/2/users/by/username/${username}`, {
      headers: { Authorization: `Bearer ${bearerToken}` },
      params: { 'user.fields': 'created_at,profile_image_url,public_metrics' },
    });

    const posts = await axios.get(`https://api.x.com/2/users/${user.data.data.id}/tweets`, {
      headers: { Authorization: `Bearer ${bearerToken}` },
      params: { max_results: 10, 'tweet.fields': 'created_at,text' },
    });

    console.log(`[INFO] Fetched user data for ${username}`);
    res.json({
      username: user.data.data.username,
      profile_image_url: user.data.data.profile_image_url,
      followers: user.data.data.public_metrics.followers_count,
      following: user.data.data.public_metrics.following_count,
      created_at: user.data.data.created_at,
      posts: posts.data.data || [],
    });
  } catch (error) {
    console.error(`[ERROR] Failed to fetch user data for ${req.params.username}:`, error.message, error.response?.data || error.stack);
    res.status(500).json({ error: 'Failed to fetch user data', details: error.message });
  }
});

// Proxy endpoint for Pump.fun King of the Hill
app.get('/proxy/king-of-the-hill', async (req, res) => {
  try {
    const response = await axios.get('https://frontend-api-v3.pump.fun/coins/king-of-the-hill?includeNsfw=false', {
      headers: { 'User-Agent': 'Mozilla/5.0' },
    });
    console.log('[INFO] Fetched King of the Hill data from Pump.fun');
    res.json(response.data);
  } catch (error) {
    console.error('[ERROR] Error fetching King of the Hill data:', error.message, error.response?.data || error.stack);
    res.status(500).json({ error: 'Failed to fetch token data', details: error.message });
  }
});

// Proxy endpoint for Pump.fun latest trades
app.get('/proxy/trades/latest', async (req, res) => {
  try {
    const response = await axios.get('https://frontend-api-v3.pump.fun/trades/latest', {
      headers: { 'User-Agent': 'Mozilla/5.0' },
    });
    console.log('[INFO] Fetched latest trades from Pump.fun');
    res.json(Array.isArray(response.data) ? response.data : [response.data]);
  } catch (error) {
    console.error('[ERROR] Error fetching latest trades:', error.message, error.response?.data || error.stack);
    res.status(500).json({ error: 'Failed to fetch latest trades', details: error.message });
  }
});

// Axiom Trade tracked wallets endpoint
app.get('/api/tracked-wallets', async (req, res) => {
  const mockData = [
    {
      transactionCreatedAt: new Date().toISOString(),
      type: 'buy',
      priceUsd: 0.0001,
      tokenImage: 'https://example.com/token.png',
      tokenName: 'MockToken',
      pairAddress: 'mockPairAddress',
      totalSol: 1.2345,
      totalUsd: 123.45,
      protocol: 'mockProtocol',
      tokenAddress: 'mockTokenAddress'
    }
  ];

  try {
    // Check if the token is expired
    if (Date.now() >= axiomTokenExpiry) {
      console.log('[INFO] Axiom access token expired, refreshing...');
      const success = await refreshAccessToken();
      if (!success) {
        console.warn('[WARN] Token refresh failed, returning mock data as fallback');
        return res.status(200).json(mockData);
      }
    }

    let response = await axios.get('https://api4.axiom.trade/tracked-wallet-transactions', {
      headers: {
        'accept': 'application/json, text/plain, */*',
        'origin': 'https://axiom.trade',
        'referer': 'https://axiom.trade/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Cookie': `auth-refresh-token=${axiomAuthRefreshToken}; auth-access-token=${axiomAuthAccessToken}`
      }
    });

    console.log('[INFO] Successfully fetched tracked wallet transactions from Axiom Trade');
    res.json(response.data);
  } catch (error) {
    if (error.response && (error.response.status === 401 || error.response.status === 434)) {
      console.log(`[INFO] Received ${error.response.status} from Axiom Trade API, attempting to refresh token...`);
      if (await refreshAccessToken()) {
        try {
          const response = await axios.get('https://api4.axiom.trade/tracked-wallet-transactions', {
            headers: {
              'accept': 'application/json, text/plain, */*',
              'origin': 'https://axiom.trade',
              'referer': 'https://axiom.trade/',
              'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
              'Cookie': `auth-refresh-token=${axiomAuthRefreshToken}; auth-access-token=${axiomAuthAccessToken}`
            }
          });
          console.log('[INFO] Successfully fetched tracked wallet transactions after token refresh');
          res.json(response.data);
        } catch (retryError) {
          console.error('[ERROR] Error after token refresh:', retryError.message, retryError.response?.data || retryError.stack);
          console.warn('[WARN] Returning mock data as fallback due to repeated Axiom Trade API failure');
          res.status(200).json(mockData);
        }
      } else {
        console.warn('[WARN] Token refresh failed, returning mock data as fallback');
        res.status(200).json(mockData);
      }
    } else {
      console.error('[ERROR] Error fetching tracked wallet transactions:', error.message, error.response?.data || error.stack);
      console.warn('[WARN] Returning mock data as fallback due to Axiom Trade API failure');
      res.status(200).json(mockData);
    }
  }
});

// Signal endpoints (Discord signals)
app.post('/api/discord-signals', (req, res) => {
  try {
    const newSignal = { ...req.body, timestamp: Date.now() };
    if (discordSignals.length >= 8) discordSignals.shift();
    discordSignals.push(newSignal);
    console.log('[INFO] Stored new Discord signal');
    res.status(200).json({ message: 'Signal stored successfully' });
  } catch (error) {
    console.error('[ERROR] Failed to store Discord signal:', error.message, error.stack);
    res.status(500).json({ error: 'Failed to store signal', details: error.message });
  }
});

app.get('/api/discord-signals', (req, res) => {
  if (!discordSignals.length) {
    console.warn('[WARN] No Discord signals available');
    return res.status(404).json({ error: 'No Discord signals available' });
  }
  const now = Date.now();
  discordSignals = discordSignals.filter(signal => (now - signal.timestamp) <= 60 * 60 * 1000);
  console.log('[INFO] Fetched Discord signals');
  res.json(discordSignals);
});

// Signal endpoints (Token sentiment signals)
app.post('/api/token-sentimentx', (req, res) => {
  try {
    const newSignal = {
      ...req.body,
      timestamp: Date.now(),
      author: {
        name: 'boncatBT',
        icon_url: 'https://pbs.twimg.com/profile_images/1906453491888898048/J9itYmnr_400x400.jpg'
      }
    };
    if (tokenSentimentSignals.length >= 50) tokenSentimentSignals.shift();
    tokenSentimentSignals.push(newSignal);
    console.log('[INFO] Stored new token sentiment signal');
    res.status(200).json({ message: 'Token sentiment signal stored successfully' });
  } catch (error) {
    console.error('[ERROR] Failed to store token sentiment signal:', error.message, error.stack);
    res.status(500).json({ error: 'Failed to store token sentiment signal', details: error.message });
  }
});

app.get('/api/token-sentimentx', (req, res) => {
  if (!tokenSentimentSignals.length) {
    console.warn('[WARN] No token sentiment signals available');
    return res.status(404).json({ error: 'No token sentiment signals available' });
  }
  const now = Date.now();
  tokenSentimentSignals = tokenSentimentSignals.filter(signal => (now - signal.timestamp) <= 30 * 60 * 1000);
  console.log('[INFO] Fetched token sentiment signals');
  res.json(tokenSentimentSignals);
});

// Signal endpoints (Base signals)
app.post('/api/base-signals', (req, res) => {
  try {
    const newSignal = { ...req.body, timestamp: Date.now() };
    if (baseSignals.length >= 6) baseSignals.shift();
    baseSignals.push(newSignal);
    console.log('[INFO] Stored new base signal');
    res.status(200).json({ message: 'Base signal stored successfully' });
  } catch (error) {
    console.error('[ERROR] Failed to store base signal:', error.message, error.stack);
    res.status(500).json({ error: 'Failed to store base signal', details: error.message });
  }
});

app.get('/api/base-signals', (req, res) => {
  if (!baseSignals.length) {
    console.warn('[WARN] No base signals available');
    return res.status(404).json({ error: 'No base signals available' });
  }
  const now = Date.now();
  baseSignals = baseSignals.filter(signal => (now - signal.timestamp) <= 2 * 60 * 60 * 1000);
  console.log('[INFO] Fetched base signals');
  res.json(baseSignals);
});

app.post('/api/solana-chat', async (req, res) => {
  const { message } = req.body;
  if (!message) {
    console.warn('[WARN] Message missing in request body');
    return res.status(400).json({ error: 'Message is required' });
  }

  try {
    const response = await axios.post('https://boncatxbt.fun/api/chat', { message }, {
      headers: { 'Content-Type': 'application/json' },
      timeout: 10000
    });
    console.log('[INFO] Fetched chat response from Solana Analyzer');
    res.json(response.data);
  } catch (error) {
    console.error('[ERROR] Error fetching chat response:', error.message, error.response?.data || error.stack);
    res.status(500).json({ error: 'Failed to fetch chat response', details: error.message });
  }
});

app.get('/api/solana-chat/echo', (req, res) => {
  res.json({ status: 'ok', message: 'I had root access to existence' });
});

// Health check endpoint
app.get('/health', (req, res) => {
  console.log('[INFO] Health check requested');
  res.status(200).json({ status: 'OK', message: 'Server is running' });
});

// Proxy endpoint for Axiom Trade portfolio data
app.get('/api/proxy-axiom-portfolio', async (req, res) => {
  const { walletAddress, isOtherWallet } = req.query;

  if (!walletAddress) {
    console.warn('[WARN] Wallet address missing in query parameters');
    return res.status(400).json({ error: 'Wallet address is required' });
  }

  try {
    // Check if the token is expired
    if (Date.now() >= axiomTokenExpiry) {
      console.log('[INFO] Axiom access token expired, refreshing...');
      const success = await refreshAccessToken();
      if (!success) {
        console.error('[ERROR] Failed to refresh Axiom access token');
        return res.status(500).json({ error: 'Failed to refresh Axiom access token' });
      }
    }

    // Construct the Axiom Trade API URL
    const axiomUrl = `https://api3.axiom.trade/portfolio?walletAddress=${walletAddress}&isOtherWallet=${isOtherWallet || 'true'}`;
    
    // Make the request to Axiom Trade API
    const response = await axios.get(axiomUrl, {
      headers: {
        'Authorization': `Bearer ${axiomAuthAccessToken}`,
        'accept': 'application/json, text/plain, */*',
        'origin': 'https://axiom.trade',
        'referer': 'https://axiom.trade/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Cookie': `auth-refresh-token=${axiomAuthRefreshToken}; auth-access-token=${axiomAuthAccessToken}`
      }
    });

    console.log('[INFO] Successfully fetched portfolio data from Axiom Trade');
    res.json(response.data);
  } catch (error) {
    if (error.response && (error.response.status === 401 || error.response.status === 434)) {
      console.log(`[INFO] Received ${error.response.status} from Axiom Trade API, attempting to refresh token...`);
      if (await refreshAccessToken()) {
        try {
          const axiomUrl = `https://api3.axiom.trade/portfolio?walletAddress=${walletAddress}&isOtherWallet=${isOtherWallet || 'true'}`;
          const response = await axios.get(axiomUrl, {
            headers: {
              'Authorization': `Bearer ${axiomAuthAccessToken}`,
              'accept': 'application/json, text/plain, */*',
              'origin': 'https://axiom.trade',
              'referer': 'https://axiom.trade/',
              'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
              'Cookie': `auth-refresh-token=${axiomAuthRefreshToken}; auth-access-token=${axiomAuthAccessToken}`
            }
          });
          console.log('[INFO] Successfully fetched portfolio data after token refresh');
          res.json(response.data);
        } catch (retryError) {
          console.error('[ERROR] Error after token refresh:', retryError.message, retryError.response?.data || retryError.stack);
          res.status(500).json({ error: 'Failed to fetch portfolio data after token refresh', details: retryError.message });
        }
      } else {
        console.error('[ERROR] Token refresh failed');
        res.status(500).json({ error: 'Failed to refresh Axiom access token' });
      }
    } else {
      console.error('[ERROR] Error fetching portfolio data:', error.message, error.response?.data || error.stack);
      res.status(500).json({ error: 'Failed to fetch portfolio data', details: error.message });
    }
  }
});

// Global error handler
app.use((err, req, res, next) => {
  console.error(`[ERROR] ${req.method} ${req.url}: ${err.message}`, err.stack);
  res.status(500).json({ error: 'Internal server error', details: err.message });
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`[INFO] Server running on port ${PORT}`);
});