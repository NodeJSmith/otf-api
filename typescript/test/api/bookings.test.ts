import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BookingsApi } from '../../src/api/bookings';
import { OtfHttpClient } from '../../src/client/http-client';

describe('BookingsApi', () => {
  let bookingsApi: BookingsApi;
  let mockClient: vi.Mocked<OtfHttpClient>;

  beforeEach(() => {
    mockClient = {
      workoutRequest: vi.fn(),
    } as any;

    bookingsApi = new BookingsApi(mockClient, 'test-member-uuid');
  });

  describe('getBookingNew', () => {
    it('should fetch and transform booking data correctly', async () => {
      const mockResponse = {
        bookingId: 'test-booking-id',
        checked_in: true,
        canceled: false,
        ratable: true,
        class: {
          classUuid: 'test-class-uuid',
          name: 'Orange 60 3G',
          startsAt: '2024-01-01T10:00:00Z',
          coach: {
            firstName: 'John',
            lastName: 'Doe'
          },
          studio: {
            studioUuid: 'studio-uuid',
            name: 'Test Studio'
          }
        },
        workout: {
          performanceSummaryId: 'performance-id',
          caloriesBurned: 500,
          splatPoints: 15,
          stepCount: 5000,
          activeTimeSeconds: 3600
        }
      };

      mockClient.workoutRequest.mockResolvedValue(mockResponse);

      const result = await bookingsApi.getBookingNew('test-booking-id');

      expect(result).toEqual({
        booking_id: 'test-booking-id',
        member_uuid: 'test-member-uuid',
        person_id: 'test-member-uuid',
        service_name: null,
        cross_regional: null,
        intro: null,
        checked_in: true,
        canceled: false,
        late_canceled: null,
        canceled_at: null,
        ratable: true,
        otf_class: {
          class_uuid: 'test-class-uuid',
          name: 'Orange 60 3G',
          starts_at: '2024-01-01T10:00:00Z',
          coach: 'John Doe',
          studio: {
            studio_uuid: 'studio-uuid',
            name: 'Test Studio',
            phone_number: null,
            latitude: null,
            longitude: null,
            time_zone: null,
            email: null,
            address: null,
            currency_code: null,
            mbo_studio_id: null,
          },
          class_id: null,
          class_type: null,
          starts_at_utc: null,
        },
        workout: {
          id: 'performance-id',
          performance_summary_id: 'performance-id',
          calories_burned: 500,
          splat_points: 15,
          step_count: 5000,
          active_time_seconds: 3600,
        },
        coach_rating: null,
        class_rating: null,
        paying_studio_id: null,
        mbo_booking_id: null,
        mbo_unique_id: null,
        mbo_paying_unique_id: null,
        created_at: null,
        updated_at: null,
      });

      expect(mockClient.workoutRequest).toHaveBeenCalledWith({
        method: 'GET',
        apiType: 'performance',
        path: '/v1/bookings/test-booking-id'
      });
    });

    it('should handle missing performance summary', async () => {
      const mockResponse = {
        bookingId: 'test-booking-id',
        checked_in: false,
        canceled: false,
        ratable: false
      };

      mockClient.workoutRequest.mockResolvedValue(mockResponse);

      const result = await bookingsApi.getBookingNew('test-booking-id');

      expect(result.booking_id).toBe('test-booking-id');
      expect(result.workout).toBe(null);
      expect(result.checked_in).toBe(false);
    });
  });
});