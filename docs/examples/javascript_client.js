/**
 * RAG Chatbot JavaScript Client
 * 
 * Usage:
 *   const client = new RagChatbotClient('http://localhost:8000');
 *   await client.login('username', 'password');
 *   await client.uploadDocument(file);
 *   const answer = await client.ask('What is AI?');
 */

class RagChatbotClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.token = null;
  }

  _getHeaders() {
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  async register(username, email, password, fullName = null) {
    const response = await fetch(`${this.baseUrl}/api/auth/register`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        username,
        email,
        password,
        full_name: fullName
      })
    });
    
    if (!response.ok) {
      throw new Error(`Registration failed: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${this.baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Login failed: ${response.statusText}`);
    }
    
    const data = await response.json();
    this.token = data.access_token;
    return this.token;
  }

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.baseUrl}/api/documents/upload`, {
      method: 'POST',
      headers: {'Authorization': `Bearer ${this.token}`},
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async listDocuments() {
    const response = await fetch(`${this.baseUrl}/api/documents`, {
      headers: this._getHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Failed to list documents: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.documents;
  }

  async deleteDocument(filename) {
    const response = await fetch(`${this.baseUrl}/api/documents/${filename}`, {
      method: 'DELETE',
      headers: this._getHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete document: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async ask(question, searchMode = 'hybrid', topK = 5) {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify({
        question,
        search_mode: searchMode,
        top_k: topK
      })
    });
    
    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async createApiKey(name, permissions = ['read', 'write'], rateLimit = 100) {
    const response = await fetch(`${this.baseUrl}/api/keys`, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify({
        name,
        permissions,
        rate_limit: rateLimit
      })
    });
    
    if (!response.ok) {
      throw new Error(`Failed to create API key: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async getAnalytics(days = 7) {
    const response = await fetch(
      `${this.baseUrl}/api/analytics/performance?days=${days}`,
      {headers: this._getHeaders()}
    );
    
    if (!response.ok) {
      throw new Error(`Failed to get analytics: ${response.statusText}`);
    }
    
    return await response.json();
  }
}

// Example usage
(async () => {
  try {
    // Initialize client
    const client = new RagChatbotClient();
    
    // Login
    console.log('🔐 Logging in...');
    await client.login('test_user', 'test_password');
    console.log('✅ Logged in successfully');
    
    // Upload document
    console.log('\n📄 Uploading document...');
    const fileInput = document.getElementById('fileInput');
    const result = await client.uploadDocument(fileInput.files[0]);
    console.log(`✅ Uploaded: ${result.filename}`);
    
    // List documents
    console.log('\n📚 Your documents:');
    const docs = await client.listDocuments();
    docs.forEach(doc => {
      console.log(`  - ${doc.filename} (${doc.file_size} bytes)`);
    });
    
    // Ask question
    console.log('\n💬 Asking question...');
    const response = await client.ask('What is machine learning?');
    console.log(`Answer: ${response.answer}`);
    console.log(`Sources: ${response.sources.length} documents`);
    
    // Get analytics
    console.log('\n📊 Analytics:');
    const analytics = await client.getAnalytics(7);
    console.log(`  Total queries: ${analytics.total_queries}`);
    console.log(`  Avg response time: ${analytics.avg_response_time_ms.toFixed(0)}ms`);
    
  } catch (error) {
    console.error('Error:', error.message);
  }
})();

