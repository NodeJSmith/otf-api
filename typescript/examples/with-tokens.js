require('dotenv').config({ path: __dirname + '/.env' });
const { Otf } = require('../dist/index.js');

async function testWithTokens() {
  try {
    console.log('Creating OTF client with pre-extracted tokens...');
    
    // Load tokens from environment variables (set by token extractor)
    const tokens = {
      accessToken: process.env.OTF_ACCESS_TOKEN,
      idToken: process.env.OTF_ID_TOKEN,
      refreshToken: process.env.OTF_REFRESH_TOKEN,
      deviceKey: process.env.OTF_DEVICE_KEY,
      deviceGroupKey: process.env.OTF_DEVICE_GROUP_KEY,
      devicePassword: process.env.OTF_DEVICE_PASSWORD,
      memberUuid: process.env.OTF_MEMBER_UUID,
    };

    // Check if we have all required tokens
    const missing = Object.entries(tokens)
      .filter(([key, value]) => !value)
      .map(([key]) => key);
    
    if (missing.length > 0) {
      console.error('❌ Missing required environment variables:', missing.join(', '));
      console.error('Run the Python token extractor first: python token-extractor.py');
      return;
    }
    
    const otf = new Otf({ 
      usePreExtractedTokens: true,
      tokens 
    });
    
    console.log('Initializing with cached tokens...');
    await otf.initialize();
    
    console.log('Getting member details...');
    const member = await otf.member;
    
    console.log(`✅ Hello ${member.first_name}!`);
    console.log(`🏠 Home studio: ${member.home_studio.studio_name}`);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    if (error.message.includes('token')) {
      console.error('💡 Try running: python token-extractor.py');
    }
  }
}

testWithTokens();