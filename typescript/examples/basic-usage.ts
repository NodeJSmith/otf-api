import { Otf } from '../src';

async function example() {
  // Initialize client with credentials
  const otf = new Otf({
    email: 'your-email@example.com',
    password: 'your-password',
  });

  // Initialize authentication
  await otf.initialize();

  // Get member details
  const member = await otf.member;
  console.log(`Hello ${member.first_name}!`);
  console.log(`Home studio: ${member.home_studio.studio_name}`);

  // Get member's home studio UUID
  const homeStudioUuid = await otf.homeStudioUuid;
  console.log(`Home studio UUID: ${homeStudioUuid}`);
}

// Environment variable example
async function environmentExample() {
  // Set OTF_EMAIL and OTF_PASSWORD environment variables
  const otf = new Otf();
  await otf.initialize();
  
  const member = await otf.member;
  console.log(`Member: ${member.first_name} ${member.last_name}`);
}

export { example, environmentExample };