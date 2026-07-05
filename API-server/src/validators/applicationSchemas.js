import { z } from 'zod';

export const createApplicationSchema = z.object({
  resume_text: z.string().optional(),
  job_description_text: z.string().min(1, 'job_description_text is required'),
  company_name: z.string().optional().default(''),
  role_title: z.string().optional().default(''),
  recipient_email: z.string().email().optional().or(z.literal('')),
});

export const reviseSchema = z.object({
  feedback: z.string().min(1, 'feedback is required'),
  target: z.enum(['resume', 'email', 'both']).default('resume'),
});

export const draftEmailSchema = z.object({
  tone: z.string().optional().default('professional, concise, internship-friendly'),
});

export const approvalSchema = z.object({
  approval_id: z.string().optional(),
  feedback: z.string().optional().default(''),
});

export const rejectSchema = z.object({
  approval_id: z.string().optional(),
  feedback: z.string().optional().default(''),
});
