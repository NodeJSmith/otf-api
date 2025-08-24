import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MembersApi } from '../../src/api/members';
import { OtfHttpClient } from '../../src/client/http-client';

describe('MembersApi', () => {
  let membersApi: MembersApi;
  let mockClient: vi.Mocked<OtfHttpClient>;

  beforeEach(() => {
    mockClient = {
      request: vi.fn(),
    } as any;

    membersApi = new MembersApi(mockClient, 'test-member-uuid');
  });

  describe('getMemberDetail', () => {
    it('should fetch and transform member data correctly', async () => {
      const mockResponse = {
        data: {
          memberUUId: 'test-member-uuid',
          firstName: 'John',
          lastName: 'Doe',
          email: 'john.doe@example.com',
          phoneNumber: '+1234567890',
          homeStudio: {
            studioUUId: 'home-studio-uuid',
            studioName: 'Test Studio',
            studioNumber: '123',
            timeZone: 'America/New_York',
            contactEmail: 'studio@example.com',
            studioLocation: {
              addressLine1: '123 Main St',
              city: 'Test City',
              state: 'NY',
              postalCode: '12345',
              latitude: 40.7128,
              longitude: -74.0060
            }
          }
        }
      };

      mockClient.request.mockResolvedValue(mockResponse);

      const result = await membersApi.getMemberDetail();

      expect(result).toEqual({
        member_uuid: 'test-member-uuid',
        first_name: 'John',
        last_name: 'Doe',
        email: 'john.doe@example.com',
        phone_number: '+1234567890',
        home_studio: {
          studio_uuid: 'home-studio-uuid',
          studio_name: 'Test Studio',
          studio_number: '123',
          time_zone: 'America/New_York',
          contact_email: 'studio@example.com',
          studio_location: {
            address: '123 Main St',
            city: 'Test City',
            state: 'NY',
            postal_code: '12345',
            latitude: 40.7128,
            longitude: -74.0060
          }
        }
      });

      expect(mockClient.request).toHaveBeenCalledWith({
        method: 'GET',
        baseUrl: 'https://api.orangetheory.co',
        path: '/member/members/test-member-uuid',
        params: {
          include: 'memberAddresses,memberClassSummary'
        }
      });
    });

    it('should handle missing optional fields gracefully', async () => {
      const mockResponse = {
        data: {
          memberUUId: 'test-member-uuid',
          firstName: 'John',
          lastName: 'Doe'
        }
      };

      mockClient.request.mockResolvedValue(mockResponse);

      const result = await membersApi.getMemberDetail();

      expect(result.member_uuid).toBe('test-member-uuid');
      expect(result.first_name).toBe('John');
      expect(result.last_name).toBe('Doe');
      expect(result.email).toBeUndefined();
    });
  });
});