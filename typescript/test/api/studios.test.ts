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
        name: 'Test Studio',
        studio_number: '123',
        time_zone: 'America/New_York',
        contact_email: 'studio@example.com',
        location: {
          address_line1: '123 Studio St',
          city: 'Test City',
          state: 'NY',
          postal_code: '12345',
          latitude: 40.7128,
          longitude: -74.0060,
          phone_number: '+1234567890',
          address_line2: null,
          country: null,
          region: null,
          country_id: null,
          physical_country_id: null,
          physical_region: null,
        },
        distance: null,
        status: null,
        accepts_ach: null,
        accepts_american_express: null,
        accepts_discover: null,
        accepts_visa_master_card: null,
        allows_cr_waitlist: null,
        allows_dashboard_access: null,
        is_crm: null,
        is_integrated: null,
        is_mobile: null,
        is_otbeat: null,
        is_web: null,
        sms_package_enabled: null,
        studio_id: null,
        studio_physical_location_id: null,
        studio_type_id: null,
        mbo_studio_id: null,
        open_date: null,
        pricing_level: null,
        re_open_date: null,
        studio_token: null,
      });
    });

    it('should return empty model when studio not found', async () => {
      mockClient.workoutRequest.mockRejectedValue(new Error('Studio not found'));

      const result = await studiosApi.getStudioDetail('invalid-uuid');

      expect(result).toEqual({
        studio_uuid: 'invalid-uuid',
        name: null,
        studio_number: null,
        time_zone: null,
        contact_email: null,
        location: undefined,
        distance: null,
        status: null,
        accepts_ach: null,
        accepts_american_express: null,
        accepts_discover: null,
        accepts_visa_master_card: null,
        allows_cr_waitlist: null,
        allows_dashboard_access: null,
        is_crm: null,
        is_integrated: null,
        is_mobile: null,
        is_otbeat: null,
        is_web: null,
        sms_package_enabled: null,
        studio_id: null,
        studio_physical_location_id: null,
        studio_type_id: null,
        mbo_studio_id: null,
        open_date: null,
        pricing_level: null,
        re_open_date: null,
        studio_token: null,
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
      expect(result[0].name).toBe('Nearby Studio');
    });
  });
});