import { describe, it, expect, vi, beforeEach } from 'vitest';
import { WorkoutsApi } from '../../src/api/workouts';
import { OtfHttpClient } from '../../src/client/http-client';

describe('WorkoutsApi', () => {
  let workoutsApi: WorkoutsApi;
  let mockClient: vi.Mocked<OtfHttpClient>;

  beforeEach(() => {
    mockClient = {
      workoutRequest: vi.fn(),
    } as any;

    workoutsApi = new WorkoutsApi(mockClient, 'test-member-uuid');
  });

  describe('getPerformanceSummary', () => {
    it('should fetch performance summary by ID', async () => {
      const mockResponse = {
        data: {
          performanceSummaryId: 'test-summary-id',
          calories: 500,
          splats: 15,
          activeTime: 2700, // 45 minutes in seconds
          zoneTime: {
            gray: 5,
            blue: 10,
            green: 15,
            orange: 12,
            red: 3
          }
        }
      };

      mockClient.workoutRequest.mockResolvedValue(mockResponse);

      const result = await workoutsApi.getPerformanceSummary('test-summary-id');

      expect(result).toEqual({
        performance_summary_id: 'test-summary-id',
        calories: 500,
        splats: 15,
        active_time: 2700,
        zone_time: {
          gray: 5,
          blue: 10,
          green: 15,
          orange: 12,
          red: 3
        }
      });
    });
  });

  describe('getTelemetry', () => {
    it('should fetch telemetry data with max data points', async () => {
      const mockResponse = {
        data: [
          {
            createdAt: '2024-01-01T10:00:00Z',
            heartRate: 150,
            zone: 'orange'
          }
        ]
      };

      mockClient.workoutRequest.mockResolvedValue(mockResponse);

      const result = await workoutsApi.getTelemetry('test-summary-id', 100);

      expect(result).toEqual([{
        created_at: '2024-01-01T10:00:00Z',
        heart_rate: 150,
        zone: 'orange'
      }]);

      expect(mockClient.workoutRequest).toHaveBeenCalledWith({
        method: 'GET',
        apiType: 'telemetry',
        path: '/telemetry/test-summary-id',
        params: { maxDataPoints: 100 }
      });
    });
  });

  describe('getOutOfStudioWorkouts', () => {
    it('should fetch out-of-studio workouts with date range', async () => {
      const mockResponse = {
        data: [
          {
            id: 'oos-workout-1',
            createdAt: '2024-01-01T10:00:00Z',
            workoutType: 'Running',
            durationMinutes: 30,
            calories: 300
          }
        ]
      };

      mockClient.workoutRequest.mockResolvedValue(mockResponse);

      const startDate = new Date('2024-01-01');
      const endDate = new Date('2024-01-31');
      
      const result = await workoutsApi.getOutOfStudioWorkouts(startDate, endDate);

      expect(result).toHaveLength(1);
      expect(result[0].id).toBe('oos-workout-1');
      expect(result[0].workout_type).toBe('Running');
    });
  });

  describe('getEquipmentData', () => {
    it('should fetch equipment statistics', async () => {
      const mockResponse = {
        data: {
          treadmill: {
            totalDistance: 100.5,
            avgPace: '7:30',
            maxSpeed: 12.0
          },
          rower: {
            totalDistance: 5000,
            avgPace: '2:15',
            maxWatts: 350
          }
        }
      };

      mockClient.workoutRequest.mockResolvedValue(mockResponse);

      const result = await workoutsApi.getEquipmentData('TREADMILL', 'thisYear');

      expect(result).toBeDefined();
      expect(mockClient.workoutRequest).toHaveBeenCalledWith({
        method: 'GET',
        apiType: 'performance',
        path: '/member/test-member-uuid/stats',
        params: {
          equipmentType: 'TREADMILL',
          timeframe: 'thisYear'
        }
      });
    });
  });
});