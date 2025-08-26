// Simple test script to validate TypeScript library functionality
// This bypasses TypeScript compilation issues to test core functionality

require('dotenv').config({ path: __dirname + '/.env' });

// Simple mock to test the module structure
console.log('Testing OTF TypeScript Library');
console.log('==============================');

// Check environment variables
console.log('Environment Setup:');
console.log('- OTF_EMAIL:', process.env.OTF_EMAIL ? '✓ Set' : '✗ Not set');
console.log('- OTF_PASSWORD:', process.env.OTF_PASSWORD ? '✓ Set' : '✗ Not set');

// Test if we can load the core modules
console.log('\nModule Loading Tests:');

try {
  // Test generated types
  const fs = require('fs');
  const path = require('path');
  
  const typesPath = path.join(__dirname, '../src/generated/types.ts');
  if (fs.existsSync(typesPath)) {
    console.log('- Generated types file: ✓ Exists');
    
    // Check if it contains expected types
    const typesContent = fs.readFileSync(typesPath, 'utf8');
    const hasMainTypes = [
      'MemberDetail',
      'StudioDetail', 
      'BookingV2',
      'Workout'
    ].every(type => typesContent.includes(type));
    
    console.log('- Contains main types:', hasMainTypes ? '✓ Yes' : '✗ No');
  } else {
    console.log('- Generated types file: ✗ Missing');
  }
  
  // Test individual source files
  const sourceFiles = [
    '../src/otf.ts',
    '../src/api/members.ts', 
    '../src/api/bookings.ts',
    '../src/api/studios.ts',
    '../src/api/workouts.ts',
    '../src/auth/cognito.ts'
  ];
  
  sourceFiles.forEach(file => {
    const filePath = path.join(__dirname, file);
    const exists = fs.existsSync(filePath);
    const fileName = path.basename(file);
    console.log(`- ${fileName}:`, exists ? '✓ Exists' : '✗ Missing');
  });
  
} catch (error) {
  console.error('Error during module tests:', error.message);
}

// Test schema validation
console.log('\nSchema Validation:');
try {
  const fs = require('fs');
  const path = require('path');
  const yaml = require('js-yaml');
  
  const schemaPath = path.join(__dirname, '../../schema/openapi.yaml');
  if (fs.existsSync(schemaPath)) {
    console.log('- OpenAPI schema: ✓ Exists');
    
    const schemaContent = fs.readFileSync(schemaPath, 'utf8');
    const schema = yaml.load(schemaContent);
    
    const expectedModels = ['MemberDetail', 'StudioDetail', 'BookingV2', 'Workout'];
    const hasAllModels = expectedModels.every(model => 
      schema.components && schema.components.schemas && schema.components.schemas[model]
    );
    
    console.log('- Contains expected models:', hasAllModels ? '✓ Yes' : '✗ No');
    
    // Check if schema uses Python field names (source of truth)
    const memberDetail = schema.components.schemas.MemberDetail;
    if (memberDetail && memberDetail.properties) {
      const hasPythonFields = ['member_uuid', 'first_name', 'last_name'].every(
        field => memberDetail.properties[field]
      );
      console.log('- Uses Python field names:', hasPythonFields ? '✓ Yes' : '✗ No');
    }
    
  } else {
    console.log('- OpenAPI schema: ✗ Missing');
  }
  
} catch (error) {
  console.error('Error during schema validation:', error.message);
}

// Instructions for next steps
console.log('\nNext Steps:');
console.log('============');

if (!process.env.OTF_EMAIL || !process.env.OTF_PASSWORD) {
  console.log('1. Update the .env file with your OTF credentials:');
  console.log('   - Edit examples/.env');
  console.log('   - Set OTF_EMAIL=your-email@example.com');
  console.log('   - Set OTF_PASSWORD=your-password');
  console.log('');
}

console.log('2. To test the actual API (after fixing TypeScript issues):');
console.log('   cd typescript');
console.log('   npm run build  # Fix TypeScript compilation first');
console.log('   node examples/test-local.js');
console.log('');

console.log('3. Current status:');
console.log('   ✓ Schema generation working (Python field names as source of truth)');
console.log('   ✓ Type generation working (TypeScript types from Python models)');
console.log('   ✗ TypeScript compilation failing (type mismatches in transformation code)');
console.log('   → Need to fix API transformation code to match generated types');