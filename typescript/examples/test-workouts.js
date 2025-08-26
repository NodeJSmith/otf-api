require('dotenv').config({ path: __dirname + '/.env' });
const { Otf } = require('../dist/index.js');

async function testWorkouts() {
  try {
    console.log('Creating OTF client...');
    const otf = new Otf();
    
    console.log('Initializing authentication...');
    await otf.initialize();
    
    console.log('Testing simple workout endpoints...');
    
    // Test lifetime stats
    try {
      const lifetimeStats = await otf.workouts.getMemberLifetimeStats();
      console.log('✅ Lifetime stats retrieved');
      const lifetimeStats_str = JSON.stringify(lifetimeStats);
      console.log(`Lifetime stats: ${lifetimeStats_str}`);
    } catch (error) {
      console.log('❌ Lifetime stats failed:', error.message);
    }
    
    // Test challenge tracker
    try {
      const challengeTracker = await otf.workouts.getChallengeTracker();
      console.log('✅ Challenge tracker retrieved');
      const challengeTracker_str = JSON.stringify(challengeTracker);
      console.log(`Challenge tracker: ${challengeTracker_str}`);
    } catch (error) {
      console.log('❌ Challenge tracker failed:', error.message);
    }
    
    // Test body composition
    try {
      const bodyComp = await otf.workouts.getBodyCompositionList();
      const bodyComp_str = JSON.stringify(bodyComp);
      console.log('✅ Body composition retrieved');
      console.log(`Body composition: ${bodyComp_str}`);
    } catch (error) {
      console.log('❌ Body composition failed:', error.message);
    }
    
    // Test telemetry endpoints
    try {
      const hrHistory = await otf.workouts.getHrHistory();
      const hrHistory_str = JSON.stringify(hrHistory);
      console.log('✅ HR history retrieved');
      console.log(`HR history: ${hrHistory_str}`);
    } catch (error) {
      console.log('❌ HR history failed:', error.message);
    }
    
    // Test performance summaries
    try {
      const perfSummaries = await otf.workouts.getPerformanceSummaries(5);
      const perfSummaries_str = JSON.stringify(perfSummaries);
      console.log('✅ Performance summaries retrieved');
      console.log(`Performance summaries: ${perfSummaries_str}`);
    } catch (error) {
      console.log('❌ Performance summaries failed:', error.message);
    }
    
    // Test complete workouts
    try {
      const workouts = await otf.workouts.getWorkouts();
      const workouts_str = JSON.stringify(workouts);
      console.log(`✅ Workouts retrieved: ${workouts.length} workouts`);
      console.log(`Workouts: ${workouts_str}`);
    } catch (error) {
      console.log('❌ Workouts failed:', error.message);
    }
    
  } catch (error) {
    console.error('Error:', error.message);
    console.error('Stack:', error.stack);
  }
}

testWorkouts();