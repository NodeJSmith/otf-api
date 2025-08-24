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
        data: {
          bookingId: 'test-booking-id',
          classUuid: 'test-class-uuid',
          status: 'booked',
          checkedIn: true,
          class: {
            className: 'Orange 60 3G',
            startDateTime: '2024-01-01T10:00:00Z',
            endDateTime: '2024-01-01T11:00:00Z',
            studio: {
              studioUUId: 'studio-uuid',
              studioName: 'Test Studio'
            }
          },
          performanceSummary: {
            performanceSummaryId: 'performance-id',
            calories: 500,
            splats: 15
          }
        }
      };

      mockClient.workoutRequest.mockResolvedValue(mockResponse);

      const result = await bookingsApi.getBookingNew('test-booking-id');

      expect(result).toEqual({
        id: 'test-booking-id',
        class_uuid: 'test-class-uuid',
        member_uuid: 'test-member-uuid',
        status: 'booked',
        checked_in: true,
        class: {
          class_name: 'Orange 60 3G',
          start_date_time: '2024-01-01T10:00:00Z',
          end_date_time: '2024-01-01T11:00:00Z',
          studio: {
            studio_uuid: 'studio-uuid',
            studio_name: 'Test Studio'
          }
        },
        performance_summary: {
          performance_summary_id: 'performance-id',
          calories: 500,
          splats: 15
        }
      });

      expect(mockClient.workoutRequest).toHaveBeenCalledWith({
        method: 'GET',
        apiType: 'performance',
        path: '/member/bookings/test-booking-id'
      });
    });

    it('should handle missing performance summary', async () => {
      const mockResponse = {
        data: {
          bookingId: 'test-booking-id',
          classUuid: 'test-class-uuid',
          status: 'booked',
          checkedIn: false
        }
      };

      mockClient.workoutRequest.mockResolvedValue(mockResponse);

      const result = await bookingsApi.getBookingNew('test-booking-id');

      expect(result.id).toBe('test-booking-id');
      expect(result.performance_summary).toBeUndefined();
      expect(result.checked_in).toBe(false);
    });
  });
});