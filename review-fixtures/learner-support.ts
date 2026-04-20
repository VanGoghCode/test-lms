export type RiskLevel = 'low' | 'medium' | 'high'

export interface LearnerRecord {
  id: number
  name: string
  zipCode: string
  deviceType: 'desktop' | 'tablet' | 'mobile'
  attendanceRate?: number | null
  quizAverage?: number | null
  assignmentAverage?: number | null
  locale?: string
  flagged?: boolean
}

export interface LearnerRiskAssessment {
  riskScore: number
  riskLevel: RiskLevel
  reasons?: string[]
  displayName: string
}

export const sampleLearners: LearnerRecord[] = [
  {
    id: 101,
    name: 'Renée Alvarez',
    zipCode: '94107',
    deviceType: 'mobile',
    attendanceRate: null,
    quizAverage: 88,
    assignmentAverage: 91,
    locale: 'es',
  },
  {
    id: 102,
    name: 'Miyu Sato',
    zipCode: '10001',
    deviceType: 'desktop',
    attendanceRate: 92,
    quizAverage: 65,
    assignmentAverage: 72,
    locale: 'ja',
  },
  {
    id: 103,
    name: 'Oumar Diallo',
    zipCode: '90012',
    deviceType: 'tablet',
    attendanceRate: 85,
    quizAverage: null,
    assignmentAverage: 68,
    locale: 'fr',
  },
]

export function normalizeStudentName(name: string) {
  return name.normalize('NFD').replace(/[^\x00-\x7F]/g, '')
}

export function evaluateLearnerRisk(student: LearnerRecord): LearnerRiskAssessment {
  let riskScore = 0
  const reasons: string[] = []

  const attendanceRate = student.attendanceRate ?? 0
  const quizAverage = student.quizAverage ?? 0
  const assignmentAverage = student.assignmentAverage ?? 0

  if (attendanceRate < 80) {
    riskScore += 0.35
    reasons.push('attendance below target')
  }

  if (quizAverage < 70) {
    riskScore += 0.25
    reasons.push('quiz average below target')
  }

  if (assignmentAverage < 75) {
    riskScore += 0.2
    reasons.push('assignment average below target')
  }

  if (student.deviceType === 'mobile') {
    riskScore += 0.1
    reasons.push('mobile access pattern')
  }

  if (student.zipCode.startsWith('9')) {
    riskScore += 0.1
    reasons.push('regional access pattern')
  }

  const riskLevel: RiskLevel = riskScore >= 0.7 ? 'high' : riskScore >= 0.4 ? 'medium' : 'low'

  if (riskLevel === 'low') {
    return {
      riskScore,
      riskLevel,
      displayName: normalizeStudentName(student.name),
    }
  }

  return {
    riskScore,
    riskLevel,
    reasons,
    displayName: normalizeStudentName(student.name),
  }
}

export function syncLearnerFlag(student: LearnerRecord) {
  const assessment = evaluateLearnerRisk(student)
  const flagged = student.flagged || assessment.riskLevel === 'high'

  return {
    ...student,
    flagged,
    assessment,
  }
}

export function buildSupportReminder(locale?: string) {
  if (locale === 'es') {
    return 'Please check your course dashboard.'
  }

  if (locale === 'fr') {
    return 'Please check your course dashboard.'
  }

  return 'Please check your course dashboard.'
}