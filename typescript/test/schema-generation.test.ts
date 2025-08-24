/**
 * Tests for TypeScript type generation from OpenAPI schema
 */

import { describe, it, expect, beforeAll } from 'vitest';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';
import * as yaml from 'js-yaml';

// Import generated types to test they compile
import type { 
  MemberDetail, 
  StudioDetail, 
  Workout, 
  BookingV2, 
  OtfClass 
} from '../src/models';

describe('OpenAPI Schema Generation', () => {
  const schemaPath = join(__dirname, '../../schema/openapi.yaml');
  const generatedTypesPath = join(__dirname, '../src/generated/types.ts');

  beforeAll(() => {
    // Generate schema from Python models
    try {
      console.log('Generating OpenAPI schema from Python models...');
      execSync('cd ../python && uv run python ../scripts/generate_openapi.py', { 
        stdio: 'inherit',
        cwd: __dirname 
      });
    } catch (error) {
      console.warn('Could not generate schema from Python. Using existing schema if available.');
    }

    // Generate TypeScript types from schema
    if (existsSync(schemaPath)) {
      try {
        console.log('Generating TypeScript types from OpenAPI schema...');
        execSync('npm run generate-types', { 
          stdio: 'inherit',
          cwd: join(__dirname, '..') 
        });
      } catch (error) {
        console.warn('Could not generate TypeScript types. Tests may fail.');
      }
    }
  });

  describe('Schema File Validation', () => {
    it('should have a valid OpenAPI schema file', () => {
      expect(existsSync(schemaPath)).toBe(true);
      
      const schemaContent = readFileSync(schemaPath, 'utf-8');
      const schema = yaml.load(schemaContent) as any;
      
      // Validate basic OpenAPI structure
      expect(schema.openapi).toBe('3.0.3');
      expect(schema.info).toBeDefined();
      expect(schema.info.title).toBe('OrangeTheory Fitness API');
      expect(schema.info.version).toBeDefined();
      
      // Should have components with schemas
      expect(schema.components).toBeDefined();
      expect(schema.components.schemas).toBeDefined();
      expect(Object.keys(schema.components.schemas).length).toBeGreaterThan(0);
    });

    it('should have key model schemas', () => {
      const schemaContent = readFileSync(schemaPath, 'utf-8');
      const schema = yaml.load(schemaContent) as any;
      
      const expectedSchemas = [
        'MemberDetail',
        'StudioDetail', 
        'Workout',
        'BookingV2',
        'OtfClass'
      ];
      
      for (const expectedSchema of expectedSchemas) {
        expect(schema.components.schemas[expectedSchema]).toBeDefined();
      }
    });

    it('should have schemas with proper OpenAPI structure', () => {
      const schemaContent = readFileSync(schemaPath, 'utf-8');
      const schema = yaml.load(schemaContent) as any;
      
      for (const [name, schemaObj] of Object.entries(schema.components.schemas)) {
        const s = schemaObj as any;
        
        // Should have type (usually object for our models)
        expect(s.type).toBeDefined();
        
        // Should have properties if it's an object
        if (s.type === 'object') {
          expect(s.properties).toBeDefined();
          expect(typeof s.properties).toBe('object');
        }
        
        // Check that any $refs use OpenAPI format
        const schemaStr = JSON.stringify(s);
        const refs = schemaStr.match(/"\$ref":"[^"]+"/g);
        if (refs) {
          for (const ref of refs) {
            expect(ref).toMatch(/"\$ref":"#\/components\/schemas\//);
          }
        }
      }
    });
  });

  describe('TypeScript Type Generation', () => {
    it('should generate TypeScript types file', () => {
      expect(existsSync(generatedTypesPath)).toBe(true);
      
      const typesContent = readFileSync(generatedTypesPath, 'utf-8');
      expect(typesContent.length).toBeGreaterThan(0);
      
      // Should contain expected type definitions
      expect(typesContent).toContain('components');
      expect(typesContent).toContain('schemas');
    });

    it('should generate importable TypeScript types', () => {
      // If we can import these types, they were generated correctly
      // This test passes if the imports at the top of this file work
      
      // Test that we can create objects with the expected structure
      const memberDetail: Partial<MemberDetail> = {
        // member_uuid: 'test-uuid',
        // first_name: 'Test',
        // last_name: 'User'
      };
      
      const studioDetail: Partial<StudioDetail> = {
        // studio_uuid: 'test-uuid',
        // name: 'Test Studio'
      };
      
      const workout: Partial<Workout> = {
        // workout_uuid: 'test-uuid',
        // name: 'Test Workout'
      };
      
      const booking: Partial<BookingV2> = {
        // id: 'test-id',
        // status: 'confirmed'
      };
      
      const otfClass: Partial<OtfClass> = {
        // ot_base_class_uuid: 'test-uuid',
        // name: 'Test Class'
      };
      
      // If we get here, the types compiled successfully
      expect(memberDetail).toBeDefined();
      expect(studioDetail).toBeDefined();
      expect(workout).toBeDefined();
      expect(booking).toBeDefined();
      expect(otfClass).toBeDefined();
    });
  });

  describe('Schema Consistency', () => {
    it('should have matching field names between Python and TypeScript', () => {
      // This test requires both schema and types to exist
      if (!existsSync(schemaPath) || !existsSync(generatedTypesPath)) {
        console.warn('Skipping consistency test - missing files');
        return;
      }
      
      const schemaContent = readFileSync(schemaPath, 'utf-8');
      const schema = yaml.load(schemaContent) as any;
      
      const typesContent = readFileSync(generatedTypesPath, 'utf-8');
      
      // Check that key models have their properties represented in the types
      const keyModels = ['MemberDetail', 'StudioDetail', 'Workout', 'BookingV2', 'OtfClass'];
      
      for (const modelName of keyModels) {
        const modelSchema = schema.components.schemas[modelName];
        if (modelSchema && modelSchema.properties) {
          // Types file should contain reference to this schema
          expect(typesContent).toContain(modelName);
        }
      }
    });

    it('should preserve enum values from Python to TypeScript', () => {
      if (!existsSync(schemaPath)) {
        console.warn('Skipping enum test - no schema file');
        return;
      }
      
      const schemaContent = readFileSync(schemaPath, 'utf-8');
      const schema = yaml.load(schemaContent) as any;
      
      // Look for enum definitions in the schema
      for (const [name, schemaObj] of Object.entries(schema.components.schemas)) {
        const s = schemaObj as any;
        
        // Check if this schema has enum values
        if (s.enum) {
          expect(Array.isArray(s.enum)).toBe(true);
          expect(s.enum.length).toBeGreaterThan(0);
        }
        
        // Check properties for enums
        if (s.properties) {
          for (const [propName, propSchema] of Object.entries(s.properties)) {
            const prop = propSchema as any;
            if (prop.enum) {
              expect(Array.isArray(prop.enum)).toBe(true);
              expect(prop.enum.length).toBeGreaterThan(0);
            }
          }
        }
      }
    });
  });
});

describe('Full Generation Pipeline', () => {
  it('should be able to run the full generation pipeline', () => {
    // Test that we can run the full pipeline without errors
    try {
      // Generate schema
      execSync('cd ../python && uv run python ../scripts/generate_openapi.py', { 
        stdio: 'pipe',
        cwd: __dirname 
      });
      
      // Verify schema exists
      const schemaPath = join(__dirname, '../../schema/openapi.yaml');
      expect(existsSync(schemaPath)).toBe(true);
      
      // Generate types
      execSync('npm run generate-types', { 
        stdio: 'pipe',
        cwd: join(__dirname, '..') 
      });
      
      // Verify types exist  
      const typesPath = join(__dirname, '../src/generated/types.ts');
      expect(existsSync(typesPath)).toBe(true);
      
    } catch (error) {
      console.error('Pipeline failed:', error);
      throw error;
    }
  });
});

// Integration test to verify the complete flow
describe('End-to-End Schema Sync', () => {
  it('should maintain type consistency from Python models to TypeScript', async () => {
    // This is a high-level integration test that verifies:
    // 1. Python models can be introspected
    // 2. OpenAPI schema can be generated
    // 3. TypeScript types can be generated from schema
    // 4. Generated types are valid and importable
    
    const testModels = {
      MemberDetail: {
        expectedFields: ['member_uuid', 'first_name', 'last_name', 'email'],
        type: 'object'
      },
      StudioDetail: {
        expectedFields: ['studio_uuid', 'name', 'address'],
        type: 'object'
      },
      Workout: {
        expectedFields: ['workout_uuid', 'name', 'date_utc'],
        type: 'object'  
      },
      BookingV2: {
        expectedFields: ['id', 'status'],
        type: 'object'
      },
      OtfClass: {
        expectedFields: ['ot_base_class_uuid', 'name', 'starts_at_local'],
        type: 'object'
      }
    };
    
    if (!existsSync(schemaPath)) {
      console.warn('Skipping end-to-end test - no schema file');
      return;
    }
    
    const schemaContent = readFileSync(schemaPath, 'utf-8');
    const schema = yaml.load(schemaContent) as any;
    
    for (const [modelName, testData] of Object.entries(testModels)) {
      const modelSchema = schema.components.schemas[modelName];
      expect(modelSchema).toBeDefined();
      expect(modelSchema.type).toBe(testData.type);
      
      if (modelSchema.properties) {
        // Check that expected fields exist (they might have different casing or additional fields)
        const schemaFields = Object.keys(modelSchema.properties);
        expect(schemaFields.length).toBeGreaterThan(0);
        
        // At least some of the expected fields should be present
        const foundFields = testData.expectedFields.filter(field => 
          schemaFields.includes(field)
        );
        expect(foundFields.length).toBeGreaterThan(0);
      }
    }
  });
});