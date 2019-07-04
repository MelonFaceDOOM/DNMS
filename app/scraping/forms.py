from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, FloatField, DateField, BooleanField
from wtforms.validators import ValidationError, DataRequired, NumberRange
from datetime import datetime

class CreateMockDataForm(FlaskForm):
    number_of_cases = IntegerField('Number of cases', validators=[DataRequired(), NumberRange(min=1, max=1000)],
                                   default=1000)
    min_price = FloatField('minimum price', validators=[DataRequired(), NumberRange(min=0, max=1000)],
                           default=1)
    max_price = FloatField('maximum price', validators=[DataRequired(), NumberRange(min=0, max=1000)],
                           default=10)
    start_date = DateField('Start Date (dd/mm/yyyy)', format='%d/%m/%Y', validators=[DataRequired()],
                           default=datetime.strptime("01/01/2018", "%d/%m/%Y"))
    end_date = DateField('End Date (dd/mm/yyyy)', format='%d/%m/%Y', validators=[DataRequired()],
                         default=datetime.strptime("31/12/2018", "%d/%m/%Y"))
    seller = BooleanField("Include seller variable")
    origin = BooleanField("Include origin variable")
    submit = SubmitField('Submit')

    def validate_start_date(self, start_date):
        if self.start_date.data > self.end_date.data:
            raise ValidationError('Start date cannot be earlier than the end date')

    def validate_min_price(self, min_price):
        if self.min_price.data > self.max_price.data:
            raise ValidationError('Minimum price cannot be greater than maximum price')