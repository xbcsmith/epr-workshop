# Intro to CDEvents and EPR

## Overview

In this section we will cover the CDEvents and EPR concepts and how to use them.


## Introduction

This session introduces the Continuous Delivery Core Events used throughout the workshop. We'll focus on the runtime events that orchestration systems emit to describe the lifecycle of pipelines and tasks. The aim is to give you a practical understanding of the two core subjects — `pipelineRun` and `taskRun` — and the common predicates (`queued`, `started`, `finished`) that describe their state transitions.

You'll learn how these low-level CDEvents map to real-world CI/CD systems, why they are useful for observability and automation, and how to use them in exercises later in the workshop (for example: detecting failed task runs, tracking pipeline progress across distributed workers, or correlating taskRuns to their parent pipelineRun). The remainder of this document defines the subjects, their fields, and the event types you'll use in the hands-on labs.