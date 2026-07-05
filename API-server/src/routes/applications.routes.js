import { Router } from 'express';
import { uploadResumeFile } from '../middleware/upload.js';
import { asyncHandler } from '../utils/asyncHandler.js';
import {
  createApplication,
  draftEmail,
  exportDocx,
  exportPdf,
  generateTailoredCv,
  getApplication,
  listApplications,
  parseApplication,
  approveApplication,
  rejectApplication,
  requestApproval,
  reviseApplication,
  sendApplication,
} from '../controllers/applications.controller.js';

export const applicationsRouter = Router();

applicationsRouter.get('/', asyncHandler(listApplications));
applicationsRouter.post('/', uploadResumeFile, asyncHandler(createApplication));
applicationsRouter.get('/:id', asyncHandler(getApplication));
applicationsRouter.post('/:id/parse', asyncHandler(parseApplication));
applicationsRouter.post('/:id/generate', asyncHandler(generateTailoredCv));
applicationsRouter.post('/:id/revise', asyncHandler(reviseApplication));
applicationsRouter.post('/:id/draft-email', asyncHandler(draftEmail));
applicationsRouter.post('/:id/approval/request', asyncHandler(requestApproval));
applicationsRouter.post('/:id/approve', asyncHandler(approveApplication));
applicationsRouter.post('/:id/reject', asyncHandler(rejectApplication));
applicationsRouter.post('/:id/send', asyncHandler(sendApplication));
applicationsRouter.get('/:id/export/docx', asyncHandler(exportDocx));
applicationsRouter.get('/:id/export/pdf', asyncHandler(exportPdf));
