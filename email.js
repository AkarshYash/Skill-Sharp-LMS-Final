const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: process.env.SMTP_PORT,
  auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS }
});

const sendEmail = async ({ to, subject, html }) => {
  return transporter.sendMail({ from: process.env.EMAIL_FROM, to, subject, html });
};

const emailTemplates = {
  verification: (name, token) => ({
    subject: 'Verify your ELearning account',
    html: `<h2>Hi ${name},</h2><p>Click <a href="${process.env.FRONTEND_URL}/verify-email?token=${token}">here</a> to verify your email.</p>`
  }),
  resetPassword: (name, token) => ({
    subject: 'Reset your password',
    html: `<h2>Hi ${name},</h2><p>Click <a href="${process.env.FRONTEND_URL}/reset-password?token=${token}">here</a> to reset your password. Expires in 1 hour.</p>`
  }),
  courseEnrollment: (name, courseTitle) => ({
    subject: `Enrolled in ${courseTitle}`,
    html: `<h2>Hi ${name},</h2><p>You have successfully enrolled in <strong>${courseTitle}</strong>. Start learning now!</p>`
  }),
  certificateIssued: (name, courseTitle) => ({
    subject: `Certificate Issued – ${courseTitle}`,
    html: `<h2>Congratulations ${name}!</h2><p>Your certificate for <strong>${courseTitle}</strong> has been issued.</p>`
  })
};

module.exports = { sendEmail, emailTemplates };
