from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

class CurrentState(Enum):
   pre_trial_start = "Pre Trial Start"
   trial_start = "Trial Start"
   trial_end = "Trial End"
   delay_start = "Delay Start"
   delay_end = "Delay End"
   in_transit = "In Transit"
   mistrial = "Mistrial"
   rtb = "RTB"

class DelayReason(Enum):
   vendor = "Vendor"
   npc = "NPC"
   software = "Software"
   towing = "Towing"

class EventMetaData(BaseModel):
   eventStart: str = Field(description = "YYYY-MM-DDTHH:MM:SS datetime format", examples=['2024-04-01T17:32:47'])
   timeToNextEvent: str = Field(description = "HH:MM:SS format for eplased time", examples=['00:5:12'])
   runningClock: str = Field(description = "HH:MM:SS format for elapsed time", examples=['00:11:47'])

class Delay(BaseModel):
   reason: DelayReason
   predictedResolutionTime: str = Field(description="YYYY-MM-DDTHH:MM:SS datetime format", examples=['2024-04-01T17:32:47'])

class State(BaseModel):
   currentState: CurrentState
   delay: Optional[Delay] = None

#TODO: Flesh out the transcription schema
class Transcription(BaseModel):
   speechToText: List[str]

class Metric(BaseModel):
   min: float
   max: float
   avg: float

class PerformanceMetrics(BaseModel):
   timeToTranscribePerToken: Metric
   timeToInference: Metric

class Update(BaseModel):
   metadata: EventMetaData
   state: State = Field(description="The current state")
   transcription: Transcription = Field(description="List of transcriptions?")
   performanceMetrics: PerformanceMetrics

class LastUpdate(BaseModel):
   updateTime: str = Field(description = "YYYY-MM-DDTHH:MM:SS datetime format", examples=['2024-04-01T17:32:47'])
   lastState: State = Field(description="The current state")
   runID: str = Field(description="the run_id of the run to show data for")

class Run(BaseModel):
   date: str = Field(description = "MMDDYYYY date to look for audio files")
   runID: int = Field(description = "Internal runID for debugging")

class MetricTracker:
   def __init__(self):
      self.min_transcription = 9999999
      self.min_infer = 9999999
      self.max_transcription = 0
      self.max_infer = 0
      self.avg_transcription = 0
      self.avg_infer = 0
      self.num_tokens = 0
      self.num_inferences = 0
      self.total_transcribe_time = 0
      self.total_infer_time = 0

   def get_transcription_metrics(self):
      data = {
         "min" : self.min_transcription,
         "max" : self.max_transcription,
         "avg": self.avg_transcription
      }
      return data
   
   def get_inference_metrics(self):
      data = {
         "min" : self.min_infer,
         "max" : self.max_infer,
         "avg" : self.avg_infer
      }
      return data

   def update_transcriptions(self, seconds, tokens):
      self.num_tokens += tokens
      self.total_transcribe_time += seconds
      if seconds < self.min_transcription:
         self.min_transcription = seconds
      if seconds > self.max_transcription:
         self.max_transcription = seconds
      self.avg_transcription = self.total_transcribe_time / self.num_tokens

   def update_inferences(self, seconds):
      self.num_inferences += 1
      self.total_infer_time += seconds
      if seconds < self.min_infer:
         self.min_infer = seconds
      if seconds > self.max_infer:
         self.max_infer = seconds
      self.avg_infer = self.total_infer_time / self.num_inferences
