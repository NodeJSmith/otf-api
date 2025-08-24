import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Otf } from '../src/otf';
import { NoCredentialsError } from '../src/errors';

// Mock all dependencies
vi.mock('../src/auth/cognito');
vi.mock('../src/client/http-client');
vi.mock('../src/api/members');
vi.mock('../src/api/workouts');
vi.mock('../src/api/bookings');
vi.mock('../src/api/studios');

describe('Otf', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset environment variables
    delete process.env.OTF_EMAIL;
    delete process.env.OTF_PASSWORD;
  });

  describe('constructor', () => {
    it('should create instance with user credentials', () => {
      const otf = new Otf({ email: 'test@example.com', password: 'password' });
      expect(otf).toBeDefined();
      expect(otf.members).toBeDefined();
      expect(otf.workouts).toBeDefined();
      expect(otf.bookings).toBeDefined();
      expect(otf.studios).toBeDefined();
    });

    it('should create instance with environment variables', () => {
      process.env.OTF_EMAIL = 'env@example.com';
      process.env.OTF_PASSWORD = 'envpassword';
      
      const otf = new Otf();
      expect(otf).toBeDefined();
    });

    it('should throw error when no email provided', () => {
      expect(() => {
        new Otf();
      }).toThrow(NoCredentialsError);
    });

    it('should accept email without password for token-based auth', () => {
      const otf = new Otf({ email: 'test@example.com' });
      expect(otf).toBeDefined();
    });
  });

  describe('initialization', () => {
    it('should initialize authentication and API modules', async () => {
      const otf = new Otf({ email: 'test@example.com', password: 'password' });
      
      // Mock the cognito methods
      const mockAuthenticate = vi.fn().mockResolvedValue(undefined);
      const mockGetMemberUuid = vi.fn().mockReturnValue('test-member-uuid');
      
      (otf as any).cognito = {
        authenticate: mockAuthenticate,
        getMemberUuid: mockGetMemberUuid
      };

      await otf.initialize();

      expect(mockAuthenticate).toHaveBeenCalled();
      expect(mockGetMemberUuid).toHaveBeenCalled();
    });
  });

  describe('member property', () => {
    it('should return member data as promise', async () => {
      const otf = new Otf({ email: 'test@example.com', password: 'password' });
      
      const mockMemberData = {
        member_uuid: 'test-uuid',
        first_name: 'John',
        last_name: 'Doe'
      };

      // Mock the members API
      (otf as any).members = {
        getMemberDetail: vi.fn().mockResolvedValue(mockMemberData)
      };

      const member = await otf.member;
      expect(member).toEqual(mockMemberData);
    });
  });

  describe('convenience getters', () => {
    it('should provide memberUuid getter', async () => {
      const otf = new Otf({ email: 'test@example.com', password: 'password' });
      
      const mockMemberData = {
        member_uuid: 'test-uuid'
      };

      (otf as any).members = {
        getMemberDetail: vi.fn().mockResolvedValue(mockMemberData)
      };

      const memberUuid = await otf.memberUuid;
      expect(memberUuid).toBe('test-uuid');
    });

    it('should provide homeStudioUuid getter', async () => {
      const otf = new Otf({ email: 'test@example.com', password: 'password' });
      
      const mockMemberData = {
        home_studio: {
          studio_uuid: 'home-studio-uuid'
        }
      };

      (otf as any).members = {
        getMemberDetail: vi.fn().mockResolvedValue(mockMemberData)
      };

      const homeStudioUuid = await otf.homeStudioUuid;
      expect(homeStudioUuid).toBe('home-studio-uuid');
    });
  });
});