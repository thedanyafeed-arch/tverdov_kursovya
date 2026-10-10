from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from datetime import date
from docx import Document
from pathlib import Path
from app.models.contract import Contract
from app.models.real_estate_object import RealEstateObject
from app.models.user import User
from app.core.utils import UPLOADS_DIR
from app.models.property_type import PropertyType
from datetime import datetime, timezone
import os


class ContractController:
    @staticmethod
    def generate_contract(property_id: int, user_id: int, manager_id: int, session: Session):
        # Получаем объект недвижимости с предзагрузкой типа
        prop = session.exec(
            select(RealEstateObject)
            .where(RealEstateObject.id == property_id)
            .join(PropertyType)
        ).first()

        buyer = session.get(User, user_id)
        manager = session.get(User, manager_id)

        if not prop or not buyer or not manager:
            raise HTTPException(status_code=404, detail="Объект недвижимости, покупатель или менеджер не найдены")

        # Безопасное получение названия типа
        property_type_name = prop.property_type.name if prop.property_type else "—"

        # Получаем текущую дату
        today = date.today()
        day = today.day
        month_names = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля",
            5: "мая", 6: "июня", 7: "июля", 8: "августа",
            9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
        }
        month = month_names[today.month]
        year = today.year
        
        # Формируем индивидуальные характеристики объекта
        characteristics = f"Тип недвижимости: {property_type_name}; "
        characteristics += f"Общая площадь: {prop.total_area} м²; "
        characteristics += f"Этаж: {prop.floor} из {prop.floors_total}; "
        characteristics += f"Материал стен: {prop.wall_material}; "
        characteristics += f"Отделка: {prop.finishing}"
        if prop.description:
            characteristics += f"; Описание: {prop.description}"
        
        # Определяем цену (используем скидочную, если есть)
        final_price = prop.discount_price if prop.discount_price else prop.price
        price_50_percent = final_price / 2
        
        # Создаём .docx с правильным шаблоном
        doc = Document()
        
        # Заголовок
        heading = doc.add_heading('ПРЕДВАРИТЕЛЬНЫЙ ДОГОВОР КУПЛИ-ПРОДАЖИ № __________', 0)
        heading.alignment = 1  # Центрирование
        
        # Место и дата
        doc.add_paragraph()
        doc.add_paragraph('Место заключения: _________________________')
        doc.add_paragraph(f'Дата: «{day}» {month} {year} г.')
        doc.add_paragraph()
        
        # Преамбула
        doc.add_paragraph(
            'Продавец, именуемый(ая) в дальнейшем Продавец, действующий(ая) как физическое лицо, с одной стороны,'
        )
        doc.add_paragraph()
        doc.add_paragraph('и')
        doc.add_paragraph()
        doc.add_paragraph(
            f'Покупатель, именуемое(ый, ая) в дальнейшем Покупатель ({buyer.email}), действующий(ей) на основании _________ (Основание полномочий подписанта), с другой стороны,'
        )
        doc.add_paragraph()
        doc.add_paragraph(
            'вместе именуемые Стороны, а индивидуально — Сторона,'
        )
        doc.add_paragraph()
        doc.add_paragraph(
            'заключили настоящий предварительный договор купли-продажи (далее по тексту — Договор) о нижеследующем:'
        )
        doc.add_paragraph()
        
        # 1. Предмет договора
        doc.add_paragraph('1. Предмет договора', style='Heading 1')
        doc.add_paragraph()
        doc.add_paragraph(
            '1.1. В соответствии с условиями Договора Стороны обязуются заключить договор купли-продажи (далее по тексту — Договор купли-продажи), существенные условия которого указаны в статье 2 Договора.'
        )
        doc.add_paragraph()
        doc.add_paragraph('1.2. Договор купли-продажи должен быть заключен Сторонами в срок до _________ (Срок заключения договора).')
        doc.add_paragraph()
        
        # 2. Существенные условия договора купли-продажи
        doc.add_paragraph('2. Существенные условия договора купли-продажи', style='Heading 1')
        doc.add_paragraph()
        doc.add_paragraph('2.1. Стороны договорились считать существенными условиями Договора купли-продажи следующее:')
        doc.add_paragraph()
        doc.add_paragraph('2.2. В соответствии с Договором купли-продажи Продавец обязуется передать в собственность Покупателю, а Покупатель принять и оплатить недвижимое имущество (далее по тексту - Недвижимое имущество), расположенное по адресу: ' + prop.address + ', обладающее следующими индивидуальными характеристиками: ' + characteristics + '.')
        doc.add_paragraph()
        doc.add_paragraph('2.3. Право собственности Продавца на Недвижимое имущество подтверждается: _________ (Реквизиты документа на недвижимость).')
        doc.add_paragraph()
        doc.add_paragraph('2.4. Продавец гарантирует, что на дату заключения Договора купли-продажи, Недвижимое имущество принадлежит Продавцу на праве собственности, в споре и под арестом не состоит, не является предметом залога, не обременено правами третьих лиц.')
        doc.add_paragraph()
        doc.add_paragraph('2.5. Стороны пришли к соглашению, что государственную регистрацию перехода права на Недвижимое имущество по Договору купли-продажи в регистрирующем органе осуществляет Продавец.')
        doc.add_paragraph()
        doc.add_paragraph('2.6. Расходы по государственной регистрации перехода права на Недвижимое имущество по Договору купли-продажи в регистрирующем органе несет Продавец.')
        doc.add_paragraph()
        doc.add_paragraph('2.7. Недвижимое имущество подлежит передаче Продавцом непосредственно Покупателю по месту нахождения Недвижимого имущества. Передача Недвижимого имущества оформляется двусторонним актом приема-передачи, подписываемыми Сторонами или уполномоченными представителями Сторон. Акт приема-передачи является неотъемлемой частью Договора купли-продажи.')
        doc.add_paragraph()
        doc.add_paragraph('2.9. Право собственности на Недвижимое имущество переходит к Покупателю после государственной регистрации перехода права на Недвижимое имущество в порядке, установленном законодательством о государственной регистрации прав на недвижимое имущество и сделок с ним.')
        doc.add_paragraph()
        doc.add_paragraph('2.10. Недвижимое имущество должно быть передано Покупателю в соответствии с условиями Договора купли-продажи в срок до _________ (Срок передачи недвижимого имущества).')
        doc.add_paragraph()
        doc.add_paragraph('2.11. Оплата по Договору купли-продажи осуществляется в следующем порядке:')
        doc.add_paragraph()
        doc.add_paragraph('предоплата в срок до _________ (Дата предоплаты) г. в сумме _________ (Сумма предоплаты) рублей ноль копеек;')
        doc.add_paragraph('окончательный расчет в течение 5 банковских дней со дня получения Покупателем Недвижимого имущества в соответствии с условиями Договора купли-продажи в сумме _________ (Сумма расчета) рублей ноль копеек.')
        doc.add_paragraph()
        doc.add_paragraph('ИЛИ')
        doc.add_paragraph()
        doc.add_paragraph('2.12. Оплата по Договору купли-продажи осуществляется в следующем порядке:')
        doc.add_paragraph()
        doc.add_paragraph(f'50 процентов от цены Недвижимого имущества ({price_50_percent:.2f} рублей), до подачи документов для государственной регистрации перехода права на Недвижимое имущество;')
        doc.add_paragraph(f'оставшиеся 50 процентов от цены Недвижимого имущества ({price_50_percent:.2f} рублей), в течение 5 банковских дней со дня государственной регистрации перехода права на Недвижимое имущество по Договору купли-продажи.')
        doc.add_paragraph()
        doc.add_paragraph(f'2.13. Цена Недвижимого имущества по Договору купли-продажи составляет: {final_price:.2f} рублей.')
        doc.add_paragraph()
        doc.add_paragraph('2.14. Способ оплаты по Договору купли-продажи: перечисление Покупателем денежных средств в валюте Российской Федерации (рубль) на расчетный счет Продавца. При этом обязанности Покупателя в части оплаты по Договору купли-продажи считаются исполненными со дня списания денежных средств банком Покупателя со счета Покупателя.')
        doc.add_paragraph()
        
        # 3. Срок действия договора
        doc.add_paragraph('3. Срок действия договора', style='Heading 1')
        doc.add_paragraph()
        doc.add_paragraph(f'3.1. Договор вступает в силу с {day} {month} {year} г. (даты подписания его сторонами) и действует до _________ (Дата или событие).')
        doc.add_paragraph()
        
        # 4. Права и обязанности сторон
        doc.add_paragraph('4. Права и обязанности сторон', style='Heading 1')
        doc.add_paragraph()
        doc.add_paragraph('4.1. Продавец обязуется:')
        doc.add_paragraph('4.1.1. В срок, указанный в п. 1.2 Договора заключить с Покупателем Договор купли-продажи.')
        doc.add_paragraph('4.1.2. Заключить с Покупателем Договор купли-продажи на условиях, указанных в Договоре.')
        doc.add_paragraph('4.1.3. Подготовить проект Договора купли-продажи в срок до _________ (Срок подготовки проекта).')
        doc.add_paragraph('4.1.4. Известить Покупателя об одобрении протокола разногласий либо об отклонении указанного протокола в течение 10 (десяти) рабочих дней со дня получения протокола разногласий от Покупателя.')
        doc.add_paragraph()
        doc.add_paragraph('4.2. Покупатель обязуется:')
        doc.add_paragraph('4.2.1. В срок, указанный в п. 1.2 Договора заключить с Продавцом Договор купли-продажи.')
        doc.add_paragraph('4.2.2. Заключить с Продавцом Договор купли-продажи на условиях, указанных в Договоре.')
        doc.add_paragraph('4.2.3. Направить Продавцу извещение об одобрении проекта договора купли-продажи либо направить протокол разногласий к проекту договора купли-продажи в течение 10 рабочих дней со дня получения проекта договора купли-продажи от Продавца.')
        doc.add_paragraph()
        doc.add_paragraph('4.3. Продавец вправе:')
        doc.add_paragraph('4.3.1. Отказаться от заключения Договора купли-продажи в случае нарушения существенных условий Договора купли-продажи, указанных в Договоре.')
        doc.add_paragraph()
        doc.add_paragraph('4.4. Покупатель вправе:')
        doc.add_paragraph('4.4.1. Отказаться от заключения Договора купли-продажи в случае нарушения существенных условий Договора купли-продажи, указанных в Договоре.')
        doc.add_paragraph()
        
        # 5. Ответственность сторон
        doc.add_paragraph('5. Ответственность сторон', style='Heading 1')
        doc.add_paragraph()
        doc.add_paragraph('5.1. Стороны несут ответственность за неисполнение или ненадлежащее исполнение своих обязательств по Договору в соответствии с Договором и законодательством России.')
        doc.add_paragraph()
        doc.add_paragraph('5.2. Неустойка по Договору выплачивается только на основании обоснованного письменного требования Сторон.')
        doc.add_paragraph()
        doc.add_paragraph('5.3. Выплата неустойки не освобождает Стороны от выполнения обязанностей, предусмотренных Договором.')
        doc.add_paragraph()
        doc.add_paragraph('5.4. В случае уклонения одной Стороны от заключения Договора купли-продажи, другая Сторона вправе обратиться в суд с требованием о понуждении заключить Договор купли-продажи.')
        doc.add_paragraph()
        doc.add_paragraph('5.5. Сторона, не исполнившая или ненадлежащим образом исполнившая обязательства по Договору, обязана возместить другой Стороне причиненные таким неисполнением убытки. Бремя доказывания убытков лежит на потерпевшей Стороне.')
        doc.add_paragraph()
        doc.add_paragraph('5.6. В случае нарушения Продавцом обязанности, предусмотренной п. 4.1.3 Договора, Продавец обязуется выплатить Покупателю штраф в размере _________ (Размер штрафа) рублей.')
        doc.add_paragraph()
        
        # 6. Основания и порядок расторжения договора
        doc.add_paragraph('6. Основания и порядок расторжения договора', style='Heading 1')
        doc.add_paragraph()
        doc.add_paragraph('6.1. Договор может быть расторгнут по соглашению Сторон, а также в одностороннем порядке по письменному требованию одной из Сторон по основаниям, предусмотренным Договором и законодательством.')
        doc.add_paragraph()
        doc.add_paragraph('6.2. Расторжение Договора в одностороннем порядке производится только по письменному требованию Сторон в течение 30 (тридцати) календарных дней со дня получения Стороной такого требования.')
        doc.add_paragraph()
        doc.add_paragraph('6.3. Обязательства, предусмотренные Договором, прекращаются, если до окончания срока, в который Стороны должны заключить Договор купли-продажи, он не будет заключен либо одна из Сторон не направит другой Стороне предложение заключить Договор купли-продажи.')
        doc.add_paragraph()
        doc.add_paragraph('6.4. Стороны вправе расторгнуть Договор в одностороннем порядке в случаях:')
        doc.add_paragraph()
        doc.add_paragraph('6.5. В случае нарушения одной из Сторон существенных условий Договора купли-продажи, указанных в Договоре.')
        doc.add_paragraph()
        doc.add_paragraph('6.6. В случае если до окончания срока, указанного в п. 1.2 Договора, Сторона не направит другой Стороне предложение заключить Договор купли-продажи.')
        doc.add_paragraph()
        
        # 7. Разрешение споров из договора
        doc.add_paragraph('7. Разрешение споров из договора', style='Heading 1')
        doc.add_paragraph()
        doc.add_paragraph('7.1. Претензионный порядок является обязательным. Спор может быть передан на разрешение арбитражного суда после принятия сторонами мер по досудебному урегулированию по истечении тридцати календарных дней со дня направления претензии.')
        doc.add_paragraph()
        doc.add_paragraph('7.2. Споры из Договора разрешаются в судебном порядке в _________ (Наименование суда).')
        doc.add_paragraph()
        
        # 8. Форс-мажор
        doc.add_paragraph('8. Форс-мажор', style='Heading 1')
        doc.add_paragraph()
        doc.add_paragraph('8.1. Стороны освобождаются от ответственности за полное или частичное неисполнение обязательств по Договору в случае, если неисполнение обязательств явилось следствием действий непреодолимой силы, а именно: пожара, наводнения, землетрясения, забастовки, войны, действий органов государственной власти или других независящих от Сторон обстоятельств.')
        doc.add_paragraph()
        doc.add_paragraph('8.2. Если любое из таких обстоятельств непосредственно повлекло неисполнение обязательств в сроки, установленные Договором, то эти сроки соразмерно продлеваются на время действия соответствующих обстоятельств.')
        doc.add_paragraph()
        doc.add_paragraph('8.3. Если эти обстоятельства будут длиться более 1 (одного) календарного месяца, то каждая из Сторон будет вправе выступить с инициативой о расторжении Договора в связи с невозможностью исполнения. В случае принятия Сторонами решения о расторжении Договора по названному основанию ни одна из Сторон не будет иметь права на возмещение возможных убытков.')
        doc.add_paragraph()
        doc.add_paragraph('8.4. Сторона, которая не может выполнить обязательства по Договору, должна своевременно, но не позднее 5 (пяти) календарных дней после наступления обстоятельств непреодолимой силы, письменно известить другую Сторону, с предоставлением обосновывающих документов, выданных компетентными органами.')
        doc.add_paragraph()
        doc.add_paragraph('8.5. Неуведомление или несвоевременное уведомление о возникновении форс-мажорных обстоятельств, лишают Сторону права ссылаться на любые вышеуказанные обстоятельства, как на основание, освобождающее от ответственности за неисполнение обязательств.')
        doc.add_paragraph()
        doc.add_paragraph('8.6. Стороны признают, что неплатежеспособность Сторон не является форс-мажорным обстоятельством.')
        doc.add_paragraph()
        
        # 9. Прочие условия
        doc.add_paragraph('9. Прочие условия', style='Heading 1')
        doc.add_paragraph()
        doc.add_paragraph('9.1. Стороны не имеют никаких сопутствующих устных договоренностей. Содержание текста Договора полностью соответствует действительному волеизъявлению Сторон.')
        doc.add_paragraph()
        doc.add_paragraph('9.2. Вся переписка по предмету Договора, предшествующая его заключению, теряет юридическую силу со дня заключения Договора.')
        doc.add_paragraph()
        doc.add_paragraph('9.3. Стороны признают, что если какое-либо из положений Договора становится недействительным в течение срока его действия вследствие изменения законодательства, остальные положения Договора обязательны для Сторон в течение срока действия Договора.')
        doc.add_paragraph()
        doc.add_paragraph('9.4. Договор составлен в 2 (двух) подлинных экземплярах на русском языке по одному для каждой из Сторон.')
        doc.add_paragraph()
        
        # 10. Адреса, реквизиты и подписи сторон
        doc.add_paragraph('10. Адреса, реквизиты и подписи сторон', style='Heading 1')
        doc.add_paragraph()
        doc.add_paragraph('Продавец')
        doc.add_paragraph('Фамилия Имя Отчество: _________________________')
        doc.add_paragraph('Место регистрации: _________________________')
        doc.add_paragraph('Тел.: _________________________')
        doc.add_paragraph('ИНН: _________________________')
        doc.add_paragraph('паспорт: Серия/Номер ___________, выдан: _________ (Дата выдачи) г. _________ (Наименование органа)')
        doc.add_paragraph('код подразделения: _________________________')
        doc.add_paragraph('Р/сч: _________________________')
        doc.add_paragraph('Банк: _________________________')
        doc.add_paragraph('БИК: _________________________')
        doc.add_paragraph('Кор/сч: _________________________')
        doc.add_paragraph()
        doc.add_paragraph('Покупатель')
        doc.add_paragraph(f'Наименование/ФИО: {buyer.email}')
        doc.add_paragraph('Адрес: _________________________')
        doc.add_paragraph('Тел.: _________________________')
        doc.add_paragraph('ОГРН: _________________________')
        doc.add_paragraph('ИНН: _________________________')
        doc.add_paragraph('КПП: _________________________')
        doc.add_paragraph('Р/сч: _________________________')
        doc.add_paragraph('Банк: _________________________')
        doc.add_paragraph('БИК: _________________________')
        doc.add_paragraph('Кор/сч: _________________________')
        doc.add_paragraph()
        doc.add_paragraph('От имени Продавца _________________________ (Фамилия и инициалы)')
        doc.add_paragraph()
        doc.add_paragraph('От имени Покупателя _________________________ (Фамилия и инициалы)')

        # Сохраняем файл
        filename = f"contract_{property_id}_{user_id}.docx"
        contracts_dir = UPLOADS_DIR / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)
        file_path = contracts_dir / filename
        doc.save(file_path)

        # Сохраняем запись в БД
        contract = Contract(
            real_estate_object_id=property_id,
            user_id=user_id,
            manager_id=manager_id,
            contract_date=str(date.today()),
            status="создан",
            generated_file_path=str(file_path).replace("\\", "/"),
            created_at = datetime.now(timezone.utc).isoformat()
        )
        session.add(contract)
        session.commit()
        session.refresh(contract)
        return contract

    @staticmethod
    def download_contract(contract_id: int, current_user: User, session: Session):
        contract = session.get(Contract, contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Договор не найден")

        # Проверка доступа: обычный пользователь — только свои договоры; менеджер/админ — все
        if current_user.role.name not in ["manager", "admin"]:
            if contract.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="У вас нет доступа к этому договору")

        if not contract.generated_file_path:
            raise HTTPException(status_code=404, detail="Файл договора не найден")

        return FileResponse(
            path=contract.generated_file_path,
            filename=Path(contract.generated_file_path).name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    @staticmethod
    def update_contract(contract_id: int, data, session: Session, current_user: User):
        contract = session.get(Contract, contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Договор не найден")

        # Проверка доступа: только менеджер или админ
        if current_user.role.name not in ["manager", "admin"]:
            raise HTTPException(status_code=403, detail="Доступ запрещен")

        # Обновляем только переданные поля
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)

        session.add(contract)
        session.commit()
        session.refresh(contract)
        return contract

    @staticmethod
    def update_contract_full(contract_id: int, data, session: Session, current_user: User):
        contract = session.get(Contract, contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Договор не найден")

        # Проверка доступа: только менеджер или админ
        if current_user.role.name not in ["manager", "admin"]:
            raise HTTPException(status_code=403, detail="Доступ запрещен")

        # Проверяем существование связанных объектов
        property_obj = session.get(RealEstateObject, data.real_estate_object_id)
        user = session.get(User, data.user_id)
        manager = session.get(User, data.manager_id)

        if not property_obj:
            raise HTTPException(status_code=404, detail="Объект недвижимости не найден")
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        if not manager:
            raise HTTPException(status_code=404, detail="Менеджер не найден")

        # Полное обновление всех полей
        contract.real_estate_object_id = data.real_estate_object_id
        contract.user_id = data.user_id
        contract.manager_id = data.manager_id
        contract.contract_date = data.contract_date
        contract.status = data.status

        session.add(contract)
        session.commit()
        session.refresh(contract)
        return contract

    @staticmethod
    def delete_contract(contract_id: int, session: Session, current_user: User):
        contract = session.get(Contract, contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Договор не найден")

        # Проверка доступа: только менеджер или админ
        if current_user.role.name not in ["manager", "admin"]:
            raise HTTPException(status_code=403, detail="Доступ запрещен")

        # Удаляем файл
        if contract.generated_file_path and os.path.exists(contract.generated_file_path):
            os.remove(contract.generated_file_path)

        session.delete(contract)
        session.commit()
        return {"message": "Договор удален", "contract_id": contract_id}