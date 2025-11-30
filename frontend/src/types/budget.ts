export type BudgetStatus = 'draft' | 'submitted' | 'approved' | 'rejected';
export type TransactionType = 'expense' | 'allocation';

export interface Budget {
  id: string;
  budget_code: string;
  fiscal_year: number;
  category: string;
  total_amount: number;
  allocated_amount: number;
  spent_amount: number;
  status: BudgetStatus;
  breakdown: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface BudgetTransaction {
  id: string;
  budget_id: string;
  amount: number;
  description: string;
  transaction_type: TransactionType;
  maintenance_id?: string;
  created_at: string;
  approved_at?: string;
}

export interface BudgetCreateRequest {
  fiscal_year: number;
  category: string;
  total_amount: number;
  breakdown?: Record<string, any>;
}

export interface BudgetUpdateRequest {
  category?: string;
  total_amount?: number;
  breakdown?: Record<string, any>;
}

export interface BudgetTransactionCreateRequest {
  amount: number;
  description: string;
  transaction_type: TransactionType;
  maintenance_id?: string;
}
