#!/usr/bin/env python
"""
AI Web Scraping Agent - API Server
This module provides a REST API for the web scraping agent.
"""

import os
import json
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("api.log"), logging.StreamHandler()]
)
logger = logging.getLogger("WebScraperAPI")

# Import the agent
from agent import WebScraperAgent

# Initialize FastAPI app
app = FastAPI(
    title="Web Scraping Agent API",
    description="API for the autonomous web scraping agent",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize WebScraperAgent
agent = WebScraperAgent()

# Pydantic models for API requests/responses
class SelectorConfig(BaseModel):
    type: str
    selector: str
    extract: Dict[str, Dict[str, Any]]
    pagination: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, Any]] = None

class CreateJobRequest(BaseModel):
    url: str
    selectors: SelectorConfig
    job_name: Optional[str] = None
    max_pages: Optional[int] = 1

class JobResponse(BaseModel):
    job_id: str
    job_name: str
    url: str
    status: str
    created_at: str
    last_updated: str
    items_count: Optional[int] = None
    output_file: Optional[str] = None
    error: Optional[str] = None

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int

# Background task to execute jobs
def execute_job_task(job_id: str):
    """Background task to execute a job"""
    try:
        logger.info(f"Executing job {job_id} in background")
        success = agent.execute_job(job_id)
        logger.info(f"Job {job_id} {'completed successfully' if success else 'failed'}")
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {str(e)}")

# API routes
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "Web Scraping Agent API"}

@app.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED, tags=["Jobs"])
async def create_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks
):
    """Create a new scraping job"""
    try:
        # Create job
        job_id = agent.create_scraping_job(
            url=request.url,
            selectors=request.selectors.dict(),
            job_name=request.job_name
        )
        
        # Get job info
        job_info = agent.get_job_status(job_id)
        
        # Add job to background tasks for execution
        background_tasks.add_task(execute_job_task, job_id)
        
        return job_info
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating job: {str(e)}"
        )

@app.get("/jobs", response_model=JobListResponse, tags=["Jobs"])
async def list_jobs():
    """List all jobs"""
    try:
        jobs = agent.list_jobs()
        return {
            "jobs": jobs,
            "total": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing jobs: {str(e)}"
        )

@app.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
async def get_job(job_id: str):
    """Get job status by ID"""
    try:
        job_info = agent.get_job_status(job_id)
        if not job_info or job_info.get("status") == "unknown":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        return job_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting job {job_id}: {str(e)}"
        )

@app.post("/jobs/{job_id}/execute", response_model=JobResponse, tags=["Jobs"])
async def execute_job(
    job_id: str,
    background_tasks: BackgroundTasks
):
    """Execute a job by ID"""
    try:
        # Check if job exists
        job_info = agent.get_job_status(job_id)
        if not job_info or job_info.get("status") == "unknown":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Add job to background tasks for execution
        background_tasks.add_task(execute_job_task, job_id)
        
        # Update job status
        job_info["status"] = "queued"
        job_info["last_updated"] = datetime.now().isoformat()
        
        return job_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing job {job_id}: {str(e)}"
        )

@app.get("/jobs/{job_id}/download", tags=["Jobs"])
async def download_job_data(job_id: str):
    """Download job data"""
    try:
        # Check if job exists and is completed
        job_info = agent.get_job_status(job_id)
        if not job_info or job_info.get("status") == "unknown":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job_info.get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job {job_id} is not completed yet"
            )
        
        if not job_info.get("output_file") or not os.path.exists(job_info["output_file"]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Output file for job {job_id} not found"
            )
        
        # We would normally return the file here using FileResponse,
        # but for simplicity, we'll just return the file path
        return {"file_path": job_info["output_file"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading data for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading data for job {job_id}: {str(e)}"
        )

@app.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Jobs"])
async def delete_job(job_id: str):
    """Delete a job by ID"""
    try:
        # This would typically delete the job and its data
        # For now, we'll just return a success response
        return None
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting job {job_id}: {str(e)}"
        )

def start():
    """Start the API server"""
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start()