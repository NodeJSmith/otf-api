require('dotenv').config({ path: __dirname + '/.env' });
const { Otf } = require('../dist/index.js');

async function test() {
  try {
    console.log('Creating OTF client...');
    
    const otf = new Otf();
    
    console.log('Initializing authentication...');
    await otf.initialize();
    
    console.log('Getting member details...');
    const member = await otf.member;

    const member_str = JSON.stringify(member);
    console.log(`Member: ${member_str}`);
    
    console.log(`Hello ${member.first_name}!`);
    console.log(`Home studio: ${member.home_studio.studio_name}`);
    
  } catch (error) {
    console.error('Error:', error.message);
    console.error('Stack:', error.stack);
  }
}

test();
