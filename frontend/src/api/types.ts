export interface BoundingBox {
  x1: number
  y1: number
  x2: number
  y2: number
}

export interface DetectionItem {
  bbox: [number, number, number, number]
  confidence: number
  class_id?: number
  label?: string
  cx?: number
  cy?: number
  w?: number
  h?: number
}

export interface SatelliteDetectionResponse {
  status: string
  mode: string
  image_path?: string
  annotated_image_path?: string | null
  annotated_image_url?: string | null
  raw_image_url?: string | null
  ship_count: number
  detections: DetectionItem[]
  model_variant?: string
  weights_used?: string
  conf_threshold?: number
  iou_threshold?: number
  vlm_analysis?: string | { text?: string; briefing?: string; source?: string; status?: string }
  processing_time_ms?: number
}

export interface SatellitePreset {
  id: string
  name: string
  vessel_hint: string
  exists: boolean
  preview_url?: string | null
}

export interface DronePreset {
  id: string
  name: string
  vessel_hint: string
  exists: boolean
  video_url?: string | null
}

export interface VlmResult {
  source: string
  label?: string
  reasoning?: string
  fallback?: string
}

export interface TrackSummary {
  is_current?: boolean
  record_scope?: string
  tracking_observations?: number
  confirmed_identity?: boolean
  created_frame?: number
  deletion_frame?: number
  deletion_reason?: string

  display_label?: string
  uncertain?: boolean
  candidates?: Array<{ label: string; evidence_share: number }>
  vlm?: VlmResult
  tracking_state?: string
  lifecycle_state?: string
  last_measurement_frame?: number
  track_id: number
  label: string
  stability: number
  observations: number
  last_seen_frame?: number
  classification_status: 'confirmed' | 'tentative' | 'limited_evidence' | string
}

export interface DroneFrameTrack {
  observed?: boolean
  recovered?: boolean
  status?: 'DETECTED' | 'PREDICTED' | 'RECOVERED'
  lifecycle_state?: string
  seconds_since_measurement?: number
  detector_misses?: number
  inference_opportunities?: number
  velocity_units?: string
  matching_stage?: number | null
  matching_cost?: number | null
  track_id: number
  cx: number
  cy: number
  w: number
  h: number
  confidence: number
  missed: number
  age: number
  state: string
  detection_bbox?: [number, number, number, number]
  classification?: { label: string; confidence: number; vlm?: VlmResult } | null
  classification_stable?: { label: string; stability: number; observations: number } | null
}

export interface TrackingDiagnostics {
  confirmed_tracks?: number
  recovered_tracks?: number
  scene_cut?: boolean
  camera_status?: string
  inference_ran?: boolean
  events?: Array<{ event: string; track_id?: number; reason?: string }>
  solver: string
  state_labels: string[]
  stage_matches: number[]
  high_detections: number
  low_detections: number
  new_tracks: number
  coasting_tracks: number
  tracks: (DroneFrameTrack & { kalman_state: number[]; covariance_diagonal: number[] })[]
}

export interface DroneFrameResult {
  confirmed_track_count?: number
  coasting_track_count?: number
  recovered_track_count?: number
  scene_cut?: boolean
  camera_motion_status?: string
  tracking_diagnostics?: TrackingDiagnostics
  frame_index: number
  timestamp: number
  detections: DetectionItem[]
  tracks: DroneFrameTrack[]
  ship_count: number
  active_track_count: number
  processing_mode: 'lightweight' | 'standard' | 'heavy' | string
  ppo_action: number
  yolo_called: boolean
  classifier_called: boolean
  compute_cost: number
  safety_override: boolean
}

export interface DroneVideoResponse {
  track_state_counts?: { current_tracks: number; confirmed_detected: number; coasting: number; tentative: number; deleted_history: number; confirmed_identities_total: number; all_time_tracks: number }

  tracking_diagnostic_csv?: string
  detector_call_reduction_pct?: number
  tracking_velocity_units?: string
  status: string
  mode: string
  scan_mode?: string
  video_path?: string
  scenario_name?: string
  annotated_video_path?: string | null
  annotated_video_url?: string | null
  fps: number
  frame_count: number
  processed_frames: number
  resolution: {
    width: number
    height: number
  }
  status_message: string
  unique_track_count: number
  total_detections: number
  average_detections_per_frame: number
  processing_mode_counts: {
    lightweight?: number
    standard?: number
    heavy?: number
    [key: string]: number | undefined
  }
  final_track_classifications?: Record<string, { label: string; stability: number; observations: number }>
  track_summaries: Record<string, TrackSummary>
  primary_vessel?: TrackSummary | null
  yolo_calls: number
  classifier_calls: number
  estimated_compute_cost: number
  estimated_compute_reduction: number
  safety_overrides: number
  frames?: DroneFrameResult[]
}

export interface SystemHealthSubsystem {
  name: string
  status: 'online' | 'offline' | 'warning' | 'standby' | 'unknown'
  default_imgsz?: number
}

export interface SystemHealthResponse {
  status: string
  project: string
  backend?: {
    service: string
    version: string
    status: string
  }
  hardware?: {
    device: string
    cuda_available: boolean
    torch_version: string
  }
  subsystems?: {
    detector?: SystemHealthSubsystem
    tracker?: SystemHealthSubsystem
    classifier?: SystemHealthSubsystem
    scheduler?: SystemHealthSubsystem
    vlm?: SystemHealthSubsystem
  }
  ping_ms?: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  reply: string
}

export interface BenchmarkScenario {
  total_frames: number
  scan_mode?: string
  full_processing: {
    frames_processed: number
    yolo_calls: number
    estimated_compute_cost: number
    estimated_compute_reduction_pct: number
  }
  ppo_adaptive_scheduler: {
    frames_processed: number
    scan_mode?: string
    yolo_calls: number
    estimated_compute_cost: number
    estimated_compute_reduction_pct: number
    action_distribution: {
      '0': number
      '1': number
      '2': number
    }
    safety_overrides_triggered: number
    identified_vessel: string
    timestamp: string
  }
  rule_based_scheduler?: any
}

export interface MissionHistoryEntry {
  scenario: string
  video_file: string
  scan_mode: string
  vessel_class: string
  evidence_stability: string
  total_frames: number
  compute_cost: number
  compute_saved_pct: string
  modes: string
  safety_overrides: number
  timestamp: string
}

export interface DiagnosticsMetricsData {
  baseline_1024?: {
    precision?: number
    recall?: number
    mAP50?: number
    mAP50_95?: number
    inference_ms?: number
    fps?: number
    mean_localization_iou?: number
  }
  custom_1024?: {
    precision?: number
    recall?: number
    mAP50?: number
    mAP50_95?: number
    inference_ms?: number
    fps?: number
    mean_localization_iou?: number
  }
  loss_summary?: {
    yolo11n_detector?: {
      initial_train_loss?: number
      final_train_loss?: number
      min_val_loss?: number
      min_val_loss_epoch?: number
      peak_val_map50?: number
    }
    convnext_tiny_classifier?: {
      initial_train_loss?: number
      final_train_loss?: number
      initial_val_acc?: number
      final_val_acc?: number
    }
  }
}

export interface DiagnosticSample {
  name: string
  category: string
  url: string
}
