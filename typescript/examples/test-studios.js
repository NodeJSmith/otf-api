require('dotenv').config({ path: __dirname + '/.env' });
const { Otf } = require('../dist/index.js');

async function testStudios() {
  try {
    console.log('Creating OTF client...');
    const otf = new Otf();
    
    console.log('Initializing authentication...');
    await otf.initialize();
    
    console.log('Testing studios API...');
    
    // Test home studio detail
    try {
      const homeStudio = await otf.studios.getStudioDetail();
      console.log(`✅ Home studio: ${homeStudio.studio_name} (${homeStudio.studio_uuid})`);
    } catch (error) {
      console.log('❌ Home studio failed:', error.message);
    }
    
    // Test favorite studios
    try {
      const favorites = await otf.studios.getFavoriteStudios();
      console.log(`✅ Favorite studios: ${favorites.length} studios`);
    } catch (error) {
      console.log('❌ Favorite studios failed:', error.message);
    }
    
    // Test studio services
    try {
      const services = await otf.studios.getStudioServices();
      console.log(`✅ Studio services: ${services.length} services`);
    } catch (error) {
      console.log('❌ Studio services failed:', error.message);
    }
    
    // Test geo search near home studio
    try {
      const nearbyStudios = await otf.studios.searchStudiosByGeo(undefined, undefined, 25);
      console.log(`✅ Nearby studios: ${nearbyStudios.length} studios within 25 miles`);
    } catch (error) {
      console.log('❌ Nearby studios failed:', error.message);
    }
    
    // Test specific studio detail
    try {
      const member = await otf.member;
      const homeStudioUuid = member.home_studio.studio_uuid;
      const studioDetail = await otf.studios.getStudioDetail(homeStudioUuid);
      console.log(`✅ Specific studio detail: ${studioDetail.studio_name}`);
    } catch (error) {
      console.log('❌ Specific studio detail failed:', error.message);
    }
    
  } catch (error) {
    console.error('Error:', error.message);
    console.error('Stack:', error.stack);
  }
}

testStudios();