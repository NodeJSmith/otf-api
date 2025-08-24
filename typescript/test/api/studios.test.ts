import { describe, it, expect, vi, beforeEach } from 'vitest';
import { StudiosApi } from '../../src/api/studios';
import { OtfHttpClient } from '../../src/client/http-client';

describe('StudiosApi', () => {
  let studiosApi: StudiosApi;
  let mockClient: vi.Mocked<OtfHttpClient>;

  beforeEach(() => {
    mockClient = {
      workoutRequest: vi.fn(),
    } as any;

    studiosApi = new StudiosApi(mockClient, 'test-member-uuid');
  });

  describe('getStudioDetail', () => {
    it('should fetch and transform studio data correctly', async () => {
      const mockResponse = {
        data: {
          studioUUId: 'test-studio-uuid',
          studioName: 'Test Studio',
          studioNumber: '123',
          timeZone: 'America/New_York',
          contactEmail: 'studio@example.com',
          studioLocation: {
            addressLine1: '123 Studio St',
            city: 'Test City',
            state: 'NY',
            postalCode: '12345',
            latitude: 40.7128,
            longitude: -74.0060,
            phone: '+1234567890'
          }
        }
      };

      mockClient.workoutRequest.mockResolvedValue(mockResponse);

      const result = await studiosApi.getStudioDetail('test-studio-uuid');

      expect(result).toEqual({
        studio_uuid: 'test-studio-uuid',
        studio_name: 'Test Studio',
        studio_number: '123',
        time_zone: 'America/New_York',
        contact_email: 'studio@example.com',
        studio_phone_number: '+1234567890',
        studio_physical_location_id: undefined,
        studio_location: {
          address: '123 Studio St',
          city: 'Test City',
          state: 'NY',
          postal_code: '12345',
          latitude: 40.7128,
          longitude: -74.0060,
          address_line_2: undefined,
          country: undefined
        }
      });
    });

    it('should return empty model when studio not found', async () => {
      mockClient.workoutRequest.mockRejectedValue(new Error('Studio not found'));

      const result = await studiosApi.getStudioDetail('invalid-uuid');

      expect(result).toEqual({
        studio_uuid: 'invalid-uuid',
        studio_name: '',
        studio_number: '',
        time_zone: '',
        contact_email: undefined,
        studio_phone_number: undefined,
        studio_physical_location_id: undefined,
        studio_location: undefined
      });
    });
  });

  describe('getStudioServices', () => {
    it('should fetch and transform studio services', async () => {
      const mockResponse = {
        data: [
          {
            serviceUUId: 'service-uuid-1',
            name: 'Personal Training',
            price: '$100',
            qty: 1,
            onlinePrice: '$90',
            current: true,
            isDeleted: false
          }
        ]
      };

      mockClient.workoutRequest.mockResolvedValue(mockResponse);

      const result = await studiosApi.getStudioServices('test-studio-uuid');

      expect(result).toEqual([{
        service_uuid: 'service-uuid-1',
        name: 'Personal Training',
        price: '$100',
        qty: 1,
        online_price: '$90',
        current: true,
        is_deleted: false,
        tax_rate: undefined,
        created_date: undefined,
        updated_date: undefined
      }]);
    });
  });

  describe('searchStudiosByGeo', () => {
    it('should search studios by coordinates', async () => {
      const mockResponse = {
        data: {
          studios: [
            {
              studioUUId: 'nearby-studio-uuid',
              studioName: 'Nearby Studio',
              studioLocation: {
                latitude: 40.7589,
                longitude: -73.9851
              }
            }
          ],
          pagination: { totalCount: 1 }
        }
      };

      mockClient.workoutRequest.mockResolvedValue(mockResponse);

      const result = await studiosApi.searchStudiosByGeo(40.7128, -74.0060, 25);

      expect(result).toHaveLength(1);
      expect(result[0].studio_uuid).toBe('nearby-studio-uuid');
      expect(result[0].studio_name).toBe('Nearby Studio');
    });
  });
});