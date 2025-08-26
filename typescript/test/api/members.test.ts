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
          name: 'Test Studio',
          studio_number: '123',
          time_zone: 'America/New_York',
          contact_email: 'studio@example.com',
          location: {
            address_line1: '123 Main St',
            city: 'Test City',
            state: 'NY',
            postal_code: '12345',
            latitude: 40.7128,
            longitude: -74.0060,
            address_line2: null,
            country: null,
            region: null,
            country_id: null,
            phone_number: null,
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
          mbo_studio_id: null,
          open_date: null,
          pricing_level: null,
          re_open_date: null,
          studio_physical_location_id: null,
          studio_token: null,
          studio_type_id: null,
        },
        cognito_id: '',
        profile: {
          unit_of_measure: null,
          max_hr_type: null,
          manual_max_hr: null,
          formula_max_hr: null,
          automated_hr: null,
          member_profile_uuid: null,
          member_optin_flow_type_id: null,
        },
        created_by: null,
        created_date: null,
        home_studio_id: null,
        member_id: null,
        otf_acs_id: null,
        updated_by: null,
        updated_date: null,
        class_summary: null,
        addresses: null,
        studio_display_name: null,
        birth_day: null,
        gender: null,
        locale: null,
        weight: null,
        weight_units: null,
        height: null,
        height_units: null,
        address_line1: null,
        address_line2: null,
        city: null,
        state: null,
        postal_code: null,
        mbo_id: null,
        mbo_status: null,
        mbo_studio_id: null,
        mbo_unique_id: null,
        alternate_emails: null,
        cc_last4: null,
        cc_type: null,
        home_phone: null,
        intro_neccessary: null,
        is_deleted: null,
        is_member_verified: null,
        lead_prospect: null,
        max_hr: null,
        online_signup: null,
        phone_type: null,
        work_phone: null,
        year_imported: null,
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
      expect(result.email).toBe(null);
    });
  });
});